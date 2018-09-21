from unittest import TestCase
from app.tests.models.test_models import TestHost, TestGroup, TestDatacenter, TestProject, TestUser
from library.engine.errors import GroupNotFound, DatacenterNotFound, InvalidTags, InvalidAliases
from pymongo.errors import DuplicateKeyError

TEST_CUSTOM_FIELDS_G1 = [
    { "key": "field1", "value": "1" },
    { "key": "field2", "value": "2" }
]
TEST_CUSTOM_FIELDS_G2 = [
    { "key": "field2", "value": "overriden 2" },
    { "key": "field3", "value": "3" }
]
TEST_CUSTOM_FIELDS_H = [
    { "key": "hostfield", "value": "hostvalue" },
    { "key": "field3", "value": "host overriden 3"}
]

TEST_CUSTOM_FIELDS_RESULT1 = [
    {"key": "field2", "value": "overriden 2"},
    {"key": "hostfield", "value": "hostvalue"},
    {"key": "field3", "value": "host overriden 3"}
]
TEST_CUSTOM_FIELDS_RESULT2 = [
    {"key": "field1", "value": "1"},
    {"key": "field2", "value": "overriden 2"},
    {"key": "hostfield", "value": "hostvalue"},
    {"key": "field3", "value": "host overriden 3"}
]

ANSIBLE_CF1 = [
    {"key": "ansible:port", "value": "5335"},
    {"key": "ansible:proto", "value": "udp"}
]

ANSIBLE_CF2 = [
    {"key": "ansible:port", "value": "8080"},
    {"key": "ansible:description", "value": "this is a test host"}
]

ANSIBLE_RESULT = {
    "port": "8080",
    "proto": "udp",
    "description": "this is a test host"
}


class TestHostModel(TestCase):

    @classmethod
    def setUpClass(cls):
        TestProject.destroy_all()
        TestProject.ensure_indexes()
        TestGroup.destroy_all()
        TestGroup.ensure_indexes()
        TestHost.destroy_all()
        TestHost.ensure_indexes()
        cls.tproject_owner = TestUser(username='viert', password_hash='hash')
        cls.tproject_owner.save()
        cls.tproject = TestProject(name="test_project", owner_id=cls.tproject_owner._id)
        cls.tproject.save()

    @classmethod
    def tearDownClass(cls):
        TestHost.destroy_all()
        TestGroup.destroy_all()
        TestProject.destroy_all()
        TestUser.destroy_all()

    def setUp(self):
        TestHost.destroy_all()
        TestGroup.destroy_all()

    def tearDown(self):
        TestHost.destroy_all()
        TestGroup.destroy_all()

    def test_invalid_group(self):
        g = TestGroup(name="test_group", project_id=self.tproject._id)
        g.save()
        group_id = g._id
        g.destroy()
        h = TestHost(fqdn="host.example.com", group_id=group_id)
        self.assertRaises(GroupNotFound, h.save)

    def test_invalid_datacenter(self):
        g = TestGroup(name="test_group", project_id=self.tproject._id)
        g.save()
        d = TestDatacenter(name="test_datacenter")
        d.save()
        dc_id = d._id
        d.destroy()
        h = TestHost(fqdn="host.example.com", group_id=g._id, datacenter_id=dc_id)
        self.assertRaises(DatacenterNotFound, h.save)

    def test_invalid_tags(self):
        g = TestGroup(name="test_group", project_id=self.tproject._id)
        g.save()
        h = TestHost(fqdn="host.example.com", group_id=g._id, tags="invalid_tags")
        self.assertRaises(InvalidTags, h.save)

    def test_duplicate_fqdn(self):
        g = TestGroup(name="test_group", project_id=self.tproject._id)
        g.save()
        h = TestHost(fqdn="host.example.com", group_id=g._id)
        h.save()
        h = TestHost(fqdn="host.example.com", group_id=g._id)
        self.assertRaises(DuplicateKeyError, h.save)

    def test_root_datacenter(self):
        g = TestGroup(name="test_group", project_id=self.tproject._id)
        g.save()
        dc1 = TestDatacenter(name="dc1")
        dc1.save()
        dc11 = TestDatacenter(name="dc1.1")
        dc11.save()
        dc11.set_parent(dc1)
        h = TestHost(fqdn="host.example.com", group_id=g._id, datacenter_id=dc11._id)
        h.save()
        self.assertEqual(h.root_datacenter, dc1)

    def test_tags(self):
        g1 = TestGroup(name="test_group", project_id=self.tproject._id, tags=["tag1", "tag2"])
        g1.save()
        g2 = TestGroup(name="test_group2", project_id=self.tproject._id, tags=["tag2", "tag3"])
        g2.save()
        h = TestHost(fqdn="host.example.com", group_id=g2._id, tags=["tag4"])
        h.save()
        self.assertItemsEqual(["tag2", "tag3", "tag4"], h.all_tags)
        g1.add_child(g2)
        self.assertItemsEqual(["tag1", "tag2", "tag3", "tag4"], h.all_tags)

    def test_default_aliases(self):
        h1 = TestHost(fqdn="host.example.com")
        h1.save()
        h1 = TestHost.get("host.example.com")
        self.assertIs(type(h1.aliases), list)
        self.assertEqual(len(h1.aliases), 0)

    def test_invalid_aliases(self):
        h1 = TestHost(fqdn="host.example.com", aliases="host.i.example.com")
        self.assertRaises(InvalidAliases, h1.save)

    def test_aliases(self):
        h1 = TestHost(fqdn="host.example.com", aliases=["host.i.example.com"])
        h1.save()
        h1 = TestHost.get("host.example.com")
        self.assertItemsEqual(["host.i.example.com"], h1.aliases)

    def test_aliases_search(self):
        h1 = TestHost(fqdn="host.example.com", aliases=["host.i.example.com"])
        h1.save()
        h1 = TestHost.find_one({"aliases": "host.i.example.com"})
        self.assertIsNotNone(h1)

    def test_custom_fields(self):
        g1 = TestGroup(name="g1", project_id=self.tproject._id, custom_fields=TEST_CUSTOM_FIELDS_G1)
        g1.save()
        g2 = TestGroup(name="g2", project_id=self.tproject._id, custom_fields=TEST_CUSTOM_FIELDS_G2)
        g2.save()
        h = TestHost(fqdn="host.example.com", group_id=g2._id, custom_fields=TEST_CUSTOM_FIELDS_H)
        h.save()
        self.assertItemsEqual(h.all_custom_fields, TEST_CUSTOM_FIELDS_RESULT1)
        g1.add_child(g2)
        self.assertItemsEqual(h.all_custom_fields, TEST_CUSTOM_FIELDS_RESULT2)

    def test_ansible_vars(self):
        g1 = TestGroup(name="g1", project_id=self.tproject._id, custom_fields=ANSIBLE_CF1)
        g1.save()
        h = TestHost(fqdn="host.example.com", group_id=g1._id, custom_fields=ANSIBLE_CF2)
        h.save()
        self.assertDictEqual(h.ansible_vars, ANSIBLE_RESULT)
