from library.engine.errors import ParentDoesNotExist, ParentAlreadyExists, ParentCycle, InvalidCustomFields
from library.engine.errors import InvalidTags, ChildDoesNotExist, ChildAlreadyExists, GroupNotEmpty, GroupNotFound
from library.engine.errors import InvalidProjectId
from library.engine.cache import request_time_cache
from app.models.storable_model import StorableModel, now, save_required
from bson.objectid import ObjectId, InvalidId


class Group(StorableModel):

    _collection = 'groups'
    _project_class = None
    _host_class = None

    FIELDS = (
        "_id",
        "name",
        "description",
        "created_at",
        "updated_at",
        "project_id",
        "parent_ids",
        "child_ids",
        "tags",
        "custom_fields",
    )

    KEY_FIELD = "name"

    DEFAULTS = {
        "created_at": now,
        "updated_at": now,
        "parent_ids": [],
        "child_ids": [],
        "tags": [],
        "custom_fields": []
    }

    REQUIRED_FIELDS = (
        "project_id",
        "parent_ids",
        "child_ids",
        "name",
    )

    REJECTED_FIELDS = (
        "parent_ids",
        "child_ids",
        "created_at",
        "updated_at",
    )

    INDEXES = (
        "parent_ids",
        "child_ids",
        ["name", { "unique": True }],
        "tags",
        ["custom_fields.key", "custom_fields.value"]
    )

    __slots__ = FIELDS

    def __hash__(self):
        return hash(self.name + "." + str(self._id))

    @classmethod
    def _resolve_group(cls, group):
        # gets group or group_id or str with group_id
        # and return a tuple of actual (group, group_id)
        if type(group) == cls:
            group_id = group._id
        elif type(group) == ObjectId:
            group_id = group
            group = cls.find_one({ "_id": group_id })
        else:
            group_id = ObjectId(group)
            group = cls.find_one({ "_id": group_id })
        if group is None:
            raise GroupNotFound("Group %s not found" % group_id)
        return group, group_id

    @save_required
    def add_parent(self, parent):
        parent, parent_id = self._resolve_group(parent)
        if parent_id in self.parent_ids:
            raise ParentAlreadyExists("Group %s is already a parent of group %s" % (parent.name, self.name))
        if parent_id == self._id:
            raise ParentCycle("Can't make group parent of itself")
        if self in parent.get_all_parents():
            raise ParentCycle("Can't add one of (grand)child group as a parent")
        if self.project_id != parent.project_id:
            raise InvalidProjectId("Can not add parent from different project")
        parent.child_ids.append(self._id)
        self.parent_ids.append(parent._id)
        parent.save()
        self.save()

    @save_required
    def remove_parent(self, parent):
        try:
            parent, parent_id = self._resolve_group(parent)
        except GroupNotFound:
            # this can happen due to previous system bugs having allowed to have unconnected
            # ObjectIds in parent_ids
            try:
                parent_id = ObjectId(parent)
            except InvalidId:
                parent_id = parent

            if parent_id not in self.parent_ids:
                raise ParentDoesNotExist("Group %s doesn't have a parent %s" % (self.name, parent_id))
            else:
                self.parent_ids.remove(parent_id)
                self.save()
                return

        if parent_id not in self.parent_ids:
            raise ParentDoesNotExist("Group %s is not a parent of group %s" % (parent.name, self.name))
        parent.child_ids.remove(self._id)
        self.parent_ids.remove(parent._id)
        parent.save()
        self.save()

    @save_required
    def add_child(self, child):
        child, child_id = self._resolve_group(child)
        if child_id in self.child_ids:
            raise ChildAlreadyExists("Group %s is already a child of group %s" % (child.name, self.name))
        if child_id == self._id:
            raise ParentCycle("Can't make group child of itself")
        if self in child.get_all_children():
            raise ParentCycle("Can't add one of (grand)parent group as a child")
        if self.project_id != child.project_id:
            raise InvalidProjectId("Can not add child from different project")
        child.parent_ids.append(self._id)
        self.child_ids.append(child._id)
        child.save()
        self.save()

    @save_required
    def remove_child(self, child):
        try:
            child, child_id = self._resolve_group(child)
        except GroupNotFound:
            # this can happen due to previous system bugs having allowed to have unconnected
            # ObjectIds in child_ids
            try:
                child_id = ObjectId(child)
            except InvalidId:
                child_id = child

            if child_id not in self.child_ids:
                raise ChildDoesNotExist("Group %s doesn't have a child %s" % (self.name, child_id))
            else:
                self.child_ids.remove(child_id)
                self.save()
                return

        if child_id not in self.child_ids:
            raise ChildDoesNotExist("Group %s is not a child of group %s" % (child.name, self.name))
        child.parent_ids.remove(self._id)
        self.child_ids.remove(child._id)
        child.save()
        self.save()

    @save_required
    def remove_all_children(self):
        for child in self.children:
            self.child_ids.remove(child._id)
            child.parent_ids.remove(self._id)
            child.save()
        self.save()

    @save_required
    def remove_all_parents(self):
        for parent in self.parents:
            self.parent_ids.remove(parent._id)
            parent.child_ids.remove(self._id)
            parent.save()
        self.save()

    @save_required
    def remove_all_hosts(self):
        for host in self.hosts:
            host.group_id = None
            host.save()

    @property
    def hosts(self):
        return self.host_class.find({ "group_id": self._id })

    @property
    def host_ids(self):
        return [x._id for x in self.hosts.all()]

    @property
    def all_hosts(self):
        group_ids = [ self._id ] + [x._id for x in self.get_all_children()]
        return self.host_class.find({ "group_id": { "$in": group_ids } })

    @property
    def empty(self):
        return len(self.child_ids) + self.hosts.count() == 0

    @property
    def parents(self):
        if len(self.parent_ids) == 0:
            return []
        return self.__class__.find({ "_id": { "$in": self.parent_ids }}).all()

    @property
    def children(self):
        if len(self.child_ids) == 0:
            return []
        return self.__class__.find({ "_id": { "$in": self.child_ids }}).all()

    @property
    def project(self):
        if self.project_id is None:
            return None
        return self.project_class.find_one({ "_id": self.project_id })

    @property
    def modification_allowed(self):
        return self.project.modification_allowed

    @request_time_cache()
    def get_all_children(self):
        children = self.children[:]
        for child in self.children:
            children += child.get_all_children()
        return children

    @request_time_cache()
    def get_all_parents(self):
        parents = self.parents[:]
        for parent in self.parents:
            parents += parent.get_all_parents()
        return parents

    def touch(self):
        self.updated_at = now()

    def _check_tags(self):
        if type(self.tags) is not list:
            raise InvalidTags("Tags must be of array type")
        if len(set(self.tags)) != len(self.tags):
            raise InvalidTags("Tags must be unique")

    def _check_project_ids(self):
        if self.project_id is not None and self.project is None:
            raise InvalidProjectId("Project with id %s doesn't exist" % self.project_id)
        for parent in self.parents:
            if parent.project_id != self.project_id:
                raise InvalidProjectId("Group can not be in a project different from parent's project")
        for child in self.children:
            if child.project_id != self.project_id:
                raise InvalidProjectId("Group can not be in a different project than it's children")

    def _check_custom_fields(self):
        # Custom fields validation
        if type(self.custom_fields) is not list:
            raise InvalidCustomFields("Custom fields must be of array type")
        custom_keys = set()
        for cf in self.custom_fields:
            if type(cf) is not dict:
                raise InvalidCustomFields("Custom field must be a dict")
            if "key" not in cf or "value" not in cf:
                raise InvalidCustomFields("Custom field must contain key and value fields")
            else:
                if cf["key"].strip() == "":
                    raise InvalidCustomFields("Custom field key can't be empty")
                if cf["value"].strip() == "":
                    raise InvalidCustomFields("Custom field value can't be empty")
                if cf["key"] in custom_keys:
                    raise InvalidCustomFields("Key '%s' is provided more than once" % cf["key"])
                else:
                    custom_keys.add(cf["key"])

    def _before_save(self):
        self._check_project_ids()
        self._check_tags()
        self._check_custom_fields()
        if not self.is_new:
            self.touch()

    def _before_delete(self):
        if len(self.child_ids) > 0:
            raise GroupNotEmpty("Can't delete group with child groups attached")
        if self.hosts.count() > 0:
            raise GroupNotEmpty("Can't delete groups with hosts in it")
        for parent in self.parents[:]:
            self.remove_parent(parent)

    def unattach_and_destroy(self, skip_callback=False):
        self.remove_all_parents()
        self.remove_all_children()
        self.destroy(skip_callback)

    @property
    @request_time_cache()
    def all_tags(self):
        tags = set(self.tags)
        for parent in self.parents:
            tags = tags.union(parent.all_tags)
        return tags

    @property
    @request_time_cache()
    def all_custom_fields(self):
        cf_dict = {}
        for parent in self.parents:
            for cf in parent.all_custom_fields:
                cf_dict[cf["key"]] = cf["value"]
        for cf in self.custom_fields:
            cf_dict[cf["key"]] = cf["value"]
        custom_fields = []
        for k, v in cf_dict.items():
            custom_fields.append({ "key": k, "value": v })
        return custom_fields

    @property
    def project_name(self):
        project = self.project
        if project is None:
            return None
        else:
            return project.name

    @property
    def project_class(self):
        if self._project_class is None:
            from app.models import Project
            self.__class__._project_class = Project
        return self._project_class

    @property
    def host_class(self):
        if self._host_class is None:
            from app.models import Host
            self.__class__._host_class = Host
        return self._host_class

    @classmethod
    def query_by_tags_recursive(cls, tags, query={}):
        if type(tags) == "str":
            tags = [tags]
        tagged_groups = cls.find({ "tags": { "$in": tags }}).all()
        tagged_group_ids = [x._id for x in tagged_groups]
        for g in tagged_groups:
            tagged_group_ids += [x._id for x in g.get_all_children()]
        query["_id"] = {"$in": tagged_group_ids}
        return query

    @classmethod
    def find_by_tags_recursive(cls, tags):
        return cls.find(cls.query_by_tags_recursive(tags))

    def set_custom_field(self, key, value):
        i = -1
        for (ind, cf) in enumerate(self.custom_fields):
            if cf["key"] == key:
                i = ind
                break
        if i < 0:
            self.custom_fields.append({"key": key, "value": value})
        else:
            self.custom_fields[i]["value"] = value

    def remove_custom_field(self, key):
        i = -1
        for (ind, cf) in enumerate(self.custom_fields):
            if cf["key"] == key:
                i = ind
                break
        if i < 0:
            return

        self.custom_fields = self.custom_fields[:i] + self.custom_fields[i + 1:]

    def add_tag(self, tag):
        if tag in self.tags:
            return
        self.tags.append(tag)

    def remove_tag(self, tag):
        if tag not in self.tags:
            return
        self.tags.remove(tag)
