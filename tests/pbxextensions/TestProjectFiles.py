import unittest
from pbxproj.XcodeProject import *


class ProjectFilesTest(unittest.TestCase):
    def setUp(self):
        self.obj = {
            'objects': {
                '0': {'isa': 'PBXGroup', 'children': ['group1'], 'sourceTree': "<group>"},
                '1': {'isa': 'PBXNativeTarget', 'name': 'app', 'buildConfigurationList': '3',
                      'buildPhases': ['compile1']},
                '2': {'isa': 'PBXAggregatedTarget', 'name': 'report', 'buildConfigurationList': '4',
                      'buildPhases': ['compile']},
                '3': {'isa': 'XCConfigurationList', 'buildConfigurations': ['5', '6']},
                '4': {'isa': 'XCConfigurationList', 'buildConfigurations': ['7', '8']},
                '5': {'isa': 'XCBuildConfiguration', 'name': 'Release', 'buildSettings': {'base': 'a'}},
                '6': {'isa': 'XCBuildConfiguration', 'name': 'Debug', 'id': '6'},
                '7': {'isa': 'XCBuildConfiguration', 'name': 'Release', 'id': '7'},
                '8': {'isa': 'XCBuildConfiguration', 'name': 'Debug', 'id': '8'},
                # groups
                'group1': {'isa': 'PBXGroup', 'name': 'root', 'children': ['group2', 'group3']},
                'group2': {'isa': 'PBXGroup', 'name': 'app', 'children': ['file1', 'file2']},
                'group3': {'isa': 'PBXGroup', 'name': 'app', 'children': ['file3', 'group4']},
                'group4': {'isa': 'PBXGroup', 'name': 'app', 'children': []},
                'file1': {'isa': 'PBXFileReference', 'name': 'file', 'path':'file', 'sourceTree': 'SOURCE_ROOT'},
                'file2': {'isa': 'PBXFileReference', 'name': 'file', 'path':'file', 'sourceTree': 'SOURCE_ROOT'},
                'file3': {'isa': 'PBXFileReference', 'name': 'file', 'path':'file', 'sourceTree': 'SDKROOT'},
                'build_file1': {'isa': 'PBXBuildFile', 'fileRef': 'file1'},
                'build_file2': {'isa': 'PBXBuildFile', 'fileRef': 'file2'},
                'compile': {'isa': 'PBXGenericBuildPhase', 'files': ['build_file1']},
                'compile1': {'isa': 'PBXGenericBuildPhase', 'files': ['build_file2']}
            }
        }

    def testInit(self):
        with self.assertRaisesRegexp(EnvironmentError, '^This class cannot be instantiated directly'):
            ProjectFiles()

    def testAddFileUnknown(self):
        project = XcodeProject(self.obj)
        with self.assertRaisesRegexp(ValueError, '^Unknown file extension: '):
            project.add_file("file.unknowntype")

    def testAddFileUnknownAllowed(self):
        project = XcodeProject(self.obj)
        build_file = project.add_file("file.unknowntype", ignore_unknown_type=True)

        # unknown files are added as resources
        self.assertEqual(project.objects.get_objects_in_section(u'PBXResourcesBuildPhase').__len__(), 2)
        self.assertEqual(build_file.__len__(), 2)

    def testAddFileNoPath(self):
        project = XcodeProject(self.obj)
        build_file = project.add_file(".", tree=None)

        # no tree or no path cannot be added
        self.assertEqual(build_file, [])

    def testAddFileNoCreateBuildFiles(self):
        project = XcodeProject(self.obj)
        items = project.objects.__len__()
        build_file = project.add_file(".", create_build_files=False)

        # no create build file flag
        self.assertEqual(project.objects.__len__(), items)
        self.assertEqual(build_file, [])

    def testAddFileSource(self):
        project = XcodeProject(self.obj)
        build_file = project.add_file("file.m")

        # 2 source files are created 1 x target
        self.assertEqual(project.objects.get_objects_in_section(u'PBXSourcesBuildPhase').__len__(), 2)
        self.assertEqual(build_file.__len__(), 2)

    def testAddFileFrameworkEmbedded(self):
        project = XcodeProject(self.obj)
        build_file = project.add_file("file.framework", create_build_files=True, weak=True, embed_framework=True)

        # 2 source files are created 1 x target
        self.assertEqual(project.objects.get_objects_in_section(u'PBXFrameworksBuildPhase').__len__(), 2)
        self.assertEqual(project.objects.get_objects_in_section(u'PBXCopyFilesBuildPhase').__len__(), 2)
        self.assertEqual(build_file.__len__(), 4)

    def testAddFileFrameworkWithAbsolutePath(self):
        project = XcodeProject(self.obj)
        build_file = project.add_file(os.path.abspath("samples/test.framework"))

        expected_flags = ["$(SRCROOT)/tests/samples", "$(inherited)"]
        self.assertListEqual(project.objects['5'].buildSettings.FRAMEWORK_SEARCH_PATHS, expected_flags)
        self.assertListEqual(project.objects['6'].buildSettings.FRAMEWORK_SEARCH_PATHS, expected_flags)
        self.assertListEqual(project.objects['7'].buildSettings.FRAMEWORK_SEARCH_PATHS, expected_flags)
        self.assertListEqual(project.objects['8'].buildSettings.FRAMEWORK_SEARCH_PATHS, expected_flags)

    def testAddFileLibraryWithAbsolutePath(self):
        project = XcodeProject(self.obj)
        build_file = project.add_file(os.path.abspath("samples/testLibrary.a"))

        expected_flags = "$(SRCROOT)/tests/samples"
        self.assertEqual(project.objects['5'].buildSettings.LIBRARY_SEARCH_PATHS, expected_flags)
        self.assertEqual(project.objects['6'].buildSettings.LIBRARY_SEARCH_PATHS, expected_flags)
        self.assertEqual(project.objects['7'].buildSettings.LIBRARY_SEARCH_PATHS, expected_flags)
        self.assertEqual(project.objects['8'].buildSettings.LIBRARY_SEARCH_PATHS, expected_flags)

    def testAddFileWithAbsolutePathDoesNotExist(self):
        project = XcodeProject(self.obj)
        build_file = project.add_file(os.path.abspath("samples/unexistingFile.m"))

        # nothing to do if the file is absolute but doesn't exist
        self.assertListEqual(build_file, [])

    def testAddFileWithAbsolutePathOnUnknownTree(self):
        project = XcodeProject(self.obj)
        build_file = project.add_file(os.path.abspath("samples/test.framework"), tree='DEVELOPER_DIR')

        self.assertEqual(project.objects[build_file[0].fileRef].sourceTree, '<absolute>')
        self.assertEqual(project.objects[build_file[1].fileRef].sourceTree, '<absolute>')
        self.assertEqual(project.objects[build_file[2].fileRef].sourceTree, '<absolute>')
        self.assertEqual(project.objects[build_file[3].fileRef].sourceTree, '<absolute>')

    def testAddFileIfExists(self):
        project = XcodeProject(self.obj)
        build_file = project.add_file_if_doesnt_exist("file.m")

        # 2 source files are created 1 x target
        self.assertEqual(project.objects.get_objects_in_section(u'PBXSourcesBuildPhase').__len__(), 2)
        self.assertEqual(build_file.__len__(), 2)

        build_file = project.add_file_if_doesnt_exist("file.m")
        self.assertEqual(build_file, [])

    def testGetFilesByNameWithNoParent(self):
        project = XcodeProject(self.obj)
        files = project.get_files_by_name('file')

        self.assertEqual(files.__len__(), 3)

    def testGetFilesByNameWithParent(self):
        project = XcodeProject(self.obj)

        files = project.get_files_by_name('file', 'group2')
        self.assertEqual(files.__len__(), 2)

        files = project.get_files_by_name('file', 'group3')
        self.assertEqual(files.__len__(), 1)

    def testGetFileByPathWithNoTree(self):
        project = XcodeProject(self.obj)

        files = project.get_files_by_path('file')
        self.assertEqual(files.__len__(), 2)

    def testGetFileByPathWithTree(self):
        project = XcodeProject(self.obj)

        files = project.get_files_by_path('file', TreeType.SDKROOT)
        self.assertEqual(files.__len__(), 1)

    def testRemoveFileById(self):
        project = XcodeProject(self.obj)
        original = project.__str__()
        build_files = project.add_file("file.m")

        file = project.get_files_by_name('file.m')[0]
        result = project.remove_file_by_id(file.get_id())

        self.assertTrue(result)
        self.assertEqual(project.__str__(), original)

    def testRemoveFileByIdFromTarget(self):
        project = XcodeProject(self.obj)
        build_files = project.add_file("file.m")

        file = project.get_files_by_name('file.m')[0]
        result = project.remove_file_by_id(file.get_id(), target_name='report')

        self.assertTrue(result)
        self.assertIsNotNone(project.objects[file.get_id()])
        self.assertEqual(project.objects.get_objects_in_section('PBXBuildFile').__len__(), 3)
        self.assertEqual(project.objects.get_objects_in_section('PBXSourcesBuildPhase').__len__(), 1)

    def testRemoveFileByIdOnlyFiles(self):
        project = XcodeProject(self.obj)
        result = project.remove_file_by_id('group1')

        self.assertFalse(result)

    def testRemoveFilesByName(self):
        project = XcodeProject(self.obj)
        original = project.__str__()
        build_files = project.add_file("file.m")

        result = project.remove_files_by_path('file.m')

        self.assertTrue(result)
        self.assertEqual(project.__str__(), original)