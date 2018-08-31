import os
import py

class TestUtils(object):
    
    def get_test_data_dir(self):
        return py.path.local(os.path.dirname(os.path.abspath(__file__))).join('data')

    def get_resource(self, resource_name):
        resource_path = self.get_test_data_dir().join(resource_name)
        assert resource_path.check()
        return resource_path
