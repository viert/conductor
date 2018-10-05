from commands import Command
import sys
import json
from copy import copy

MODEL_PRIMARY_KEY_NAMES = {
    "host": "fqdn",
    "group": "name",
    "work_group": "name",
    "datacenter": "name"
}


class Import(Command):
    def init_argument_parser(self, parser):
        parser.add_argument("filename", type=str, nargs=1, help="name of file to import data from")
        parser.add_argument("model_type", type=str, nargs=1, choices=["work_group", "group", "host", "datacenter"],
                            help="type of the model to import")
        parser.add_argument("model_key", type=str, nargs='?', help="key of the model to import")
        parser.add_argument("-a", "--all", dest='all', action='store_true', default=False,
                            help="import all the models of given type")

    def import_host(self, import_all, model_key):
        from app.models import Host, Group
        if import_all:
            for hostname in self.data["hosts"][MODEL_PRIMARY_KEY_NAMES["host"]]:
                self.import_host(hostname)
                return None
        else:
            host = copy(self.data["hosts"][MODEL_PRIMARY_KEY_NAMES["host"]][model_key])
            existing = Host.find_one({ MODEL_PRIMARY_KEY_NAMES["host"]: model_key })

            if existing is not None:
                print "Host %s already exists, skipping" % model_key
                return existing
            else:
                if host["group_id"] is not None:
                    group = self.data["groups"]["id"][host["group_id"]]
                    group = self.import_group(False, group[MODEL_PRIMARY_KEY_NAMES["group"]])
                    host["group_id"] = group._id
                if host["datacenter_id"] is not None:
                    try:
                        dc = self.data["datacenters"]["id"][host["datacenter_id"]]
                        dc = self.import_datacenter(False, dc[MODEL_PRIMARY_KEY_NAMES["datacenter"]])
                        host["datacenter_id"] = dc._id
                    except KeyError:
                        host["datacenter_id"] = None

                del(host["_id"])
                del(host["created_at"])
                del(host["updated_at"])
                new_host = Host(**host)
                new_host.save()
                return new_host

        print "import_host", import_all, model_key

    def import_datacenter(self, import_all, model_key):
        from app.models import Datacenter
        if import_all:
            for key in self.data["datacenters"][MODEL_PRIMARY_KEY_NAMES["datacenter"]]:
                self.import_datacenter(False, key)
            return None
        else:
            datacenter = copy(self.data["datacenters"][MODEL_PRIMARY_KEY_NAMES["datacenter"]][model_key])
            existing = Datacenter.find_one({ MODEL_PRIMARY_KEY_NAMES["datacenter"]: model_key })
            if existing is not None:
                print "Datacenter '%s' already exists, skipping" % model_key
                return existing
            else:
                del(datacenter["_id"])
                if datacenter["parent_id"] is not None:
                    parent = self.data["datacenters"]["id"][datacenter["parent_id"]]
                    parent_name = parent[MODEL_PRIMARY_KEY_NAMES["datacenter"]]
                    parent = self.import_datacenter(False, parent_name)
                    datacenter["parent_id"] = parent._id
                    new_datacenter = Datacenter(**datacenter)
                    new_datacenter.save()
                    return new_datacenter

    def import_group(self, import_all, model_key):
        from app.models import Group
        if import_all:
            for key in self.data["groups"][MODEL_PRIMARY_KEY_NAMES["group"]]:
                self.import_group(False, key)
            return None
        else:
            group = copy(self.data["groups"][MODEL_PRIMARY_KEY_NAMES["group"]][model_key])
            existing = Group.find_one({ MODEL_PRIMARY_KEY_NAMES["group"]: model_key })

            child_ids = group["child_ids"][:]
            children = [self.data["groups"]["id"][id][MODEL_PRIMARY_KEY_NAMES["group"]] for id in child_ids]
            parent_ids = group["parent_ids"][:]
            parents = [self.data["groups"]["id"][id][MODEL_PRIMARY_KEY_NAMES["group"]] for id in parent_ids]
            work_group_name = self.data["work_groups"]["id"][group["work_group_id"]][MODEL_PRIMARY_KEY_NAMES["work_group"]]

            work_group = self.import_work_group(False, work_group_name)
            group_id = group["_id"]

            del(group["_id"])
            del(group["child_ids"])
            del(group["parent_ids"])
            del(group["created_at"])
            del(group["updated_at"])
            del(group["work_group_id"])

            group["work_group_id"] = work_group._id

            if existing is not None:
                print "Group '%s' already exists, skipping" % model_key
                return existing
            else:
                new_group = Group(**group)
                new_group.save()
                for child in children:
                    child = self.import_group(False, child)
                    new_group.add_child(child)
                for parent in parents:
                    parent = self.import_group(False, parent)
                    new_group.add_parent(parent)
                print "Searching for hosts"
                hosts = self.data["hosts"]["id"].values()
                hosts = [x for x in hosts if x["group_id"] == group_id]
                for host in hosts:
                    self.import_host(False, host[MODEL_PRIMARY_KEY_NAMES["host"]])
                return new_group

    def import_work_group(self, import_all, model_key):
        from app.models import WorkGroup, User
        if import_all:
            for work_group_name in self.data["work_groups"][MODEL_PRIMARY_KEY_NAMES["work_group"]]:
                self.import_work_group(False, work_group_name)
        else:
            work_group = copy(self.data["work_groups"][MODEL_PRIMARY_KEY_NAMES["work_group"]][model_key])
            existing = WorkGroup.find_one({MODEL_PRIMARY_KEY_NAMES["work_group"]: model_key})
            if existing is not None:
                print "Project '%s' already exists, skipping" % model_key
                return existing
            else:
                del(work_group["_id"])
                del(work_group["created_at"])
                del(work_group["updated_at"])
                work_group["owner_id"] = User.find_one({})._id
                work_group["member_ids"] = []
                new_work_group = WorkGroup(**work_group)
                new_work_group.save()
                return new_work_group

    def run(self):
        if self.args.model_key is None and not self.args.all:
            print "You should provide [model_key] or use '-a/--all' flag to import all the models of given type"
            sys.exit(1)

        filename = self.args.filename[0]
        model_type = self.args.model_type[0]
        import_all = self.args.all
        model_key = self.args.model_key

        print "Importing data..."
        data = json.load(open(filename))["data"]

        self.data = {
            "work_groups": {
                "id": {},
                MODEL_PRIMARY_KEY_NAMES["work_group"]: {}
            },
            "hosts": {
                "id": {},
                MODEL_PRIMARY_KEY_NAMES["host"]: {}
            },
            "groups": {
                "id": {},
                MODEL_PRIMARY_KEY_NAMES["group"]: {}
            },
            "datacenters": {
                "id": {},
                MODEL_PRIMARY_KEY_NAMES["datacenter"]: {}
            }
        }

        for host in data["hosts"]:
            self.data["hosts"]["id"][host["_id"]] = host
            self.data["hosts"][MODEL_PRIMARY_KEY_NAMES["host"]][host[MODEL_PRIMARY_KEY_NAMES["host"]]] = host
        for dc in data["datacenters"]:
            self.data["datacenters"]["id"][dc["_id"]] = dc
            self.data["datacenters"][MODEL_PRIMARY_KEY_NAMES["datacenter"]][dc[MODEL_PRIMARY_KEY_NAMES["datacenter"]]] = dc
        for group in data["groups"]:
            self.data["groups"]["id"][group["_id"]] = group
            self.data["groups"][MODEL_PRIMARY_KEY_NAMES["group"]][group[MODEL_PRIMARY_KEY_NAMES["group"]]] = group
        for work_group in data["work_groups"]:
            self.data["work_groups"]["id"][work_group["_id"]] = work_group
            self.data["work_groups"][MODEL_PRIMARY_KEY_NAMES["work_group"]][work_group[MODEL_PRIMARY_KEY_NAMES["work_group"]]] = work_group

        method_name = "import_" + model_type
        method = getattr(self, method_name)
        method(import_all, model_key)
