from .utils import getOrDefault
import datasuper as ds
from .snakemake_rule_builder import SnakemakeRuleBuilder
from .snakemake_utils import *
from .utils import *


class ResultSchema:

    def __init__(self, muRepo, pipeName, pipeVersion, schema, origin=False):
        self.muRepo = muRepo
        self.muConfig = self.muRepo.muConfig
        self.pipelineName = pipeName
        self.pipelineVersion = pipeVersion
        self.origin = origin

        # this is the name of the result type in datasuper as well
        self.name = schema['NAME']

        self.dependencies = getOrDefault(schema, 'DEPENDENCIES', [])
        self.module = getOrDefault(schema, 'MODULE', self.name)
        self.level = getOrDefault(schema, 'LEVEL', 'SAMPLE')

        self.snakeFilename = '{}.smk'.format(self.module)
        self.snakeFilepath = self.muConfig.getSnakefile(self.pipelineName,
                                                        self.pipelineVersion,
                                                        self.snakeFilename)
        self.files = {}
        files = schema['FILES']
        if type(files) == []:
            self.files = {str(i): f for i, f in enumerate(files)}
        else:
            self.files = files

    def _makeSampleLevelRegisterRule(self):
        ruleBldr = SnakemakeRuleBuilder('register_{}'.format(self.module))

        dsRepo = ds.Repo.loadRepo()
        for fname, ftype in self.files.items():
            ext = dsRepo.getFileTypeExt(ftype)
            fpattern = self._makeFilePattern(fname, ext)
            ruleBldr.addInput(fname, fpattern)

        ruleBldr.setOutput(self.getOutputFilePattern())

        resName = joinResultNameType('{sample_name}', self.name)
        ruleBldr.addParam('dsResultName', resName)
        ruleBldr.addParam('sampleName', '{sample_name}')
        ruleBldr.addParam('dsResultType', self.name)
        for fname, ftype in self.files.items():
            ruleBldr.addParam(fname, ftype)

        runStr = '''
            with ds.Repo.loadRepo() as dsrepo:
                fileRecs = {}
                for fname, fpath in input.items():
                    name = os.path.basename(fpath)
                    abspath = os.path.abspath(fpath)
                    fileType = params[fname]
                    fileRec = ds.FileRecord(dsrepo, name=name, filepath=abspath, file_type=fileType)
                    print('[DataSuper] Saving File: {}'.format(fileRec), file=sys.stderr)
                    try:
                        fileRec.save()
                    except ds.database.RecordExistsError as ree:
                        print( '[DataSuper] Record already exists, this is usually ok but the error is reproduced below: {}'.format(ree), file=sys.stderr)
                    fileRecs[fname] = name

                result = ds.ResultRecord(dsrepo,
                                         name=params.dsResultName,
                                         result_type=params.dsResultType,
                                         file_records=fileRecs)
                print('[DataSuper] Saving Result: {}'.format(result), file=sys.stderr)
                try:
                    result.save()
                except ds.database.RecordExistsError as ree:
                    print('[DataSuper] Record already exists: {}'.format(ree), file=sys.stderr)

                try:
                    sampleName = params.sampleName
                except KeyError:
                    sampleName = None
                if sampleName and (sampleName.lower() != 'none'):
                    sample = dsrepo.db.sampleTable.get(sampleName)
                    sample.addResult(params.dsResultName)
                    sample.save(modify=True)

                outStr = ' '.join(output)
                shell('touch '+outStr)

            '''
        ruleBldr.setRun(runStr)

        return str(ruleBldr)

    def _makeGroupLevelRegisterRule(self):
        ruleBldr = SnakemakeRuleBuilder('register_{}'.format(self.module))

        dsRepo = ds.Repo.loadRepo()
        for fname, ftype in self.files.items():
            ext = dsRepo.getFileTypeExt(ftype)
            fpattern = self._makeFilePattern(fname, ext)
            ruleBldr.addInput(fname, fpattern)

        ruleBldr.setOutput(self.getOutputFilePattern())

        resName = joinResultNameType('{group_name}', self.name)
        ruleBldr.addParam('dsResultName', resName)
        ruleBldr.addParam('groupName', '{group_name}')
        ruleBldr.addParam('dsResultType', self.name)
        for fname, ftype in self.files.items():
            ruleBldr.addParam(fname, ftype)

        runStr = '''
            with ds.Repo.loadRepo() as dsrepo:
                fileRecs = {}
                for fname, fpath in input.items():
                    name = os.path.basename(fpath)
                    abspath = os.path.abspath(fpath)
                    fileType = params[fname]
                    fileRec = ds.FileRecord( dsrepo, name=name, filepath=abspath, file_type=fileType)
                    print('[DataSuper] Saving File: {}'.format(fileRec), file=sys.stderr)
                    try:
                        fileRec.save()
                    except ds.database.RecordExistsError as ree:
                        print('[DataSuper] Record already exists: {}'.format(ree), file=sys.stderr)
                    fileRecs[fname] = name

                result = ds.ResultRecord( dsrepo,
                                          name=params.dsResultName,
                                          result_type=params.dsResultType,
                                          file_records=fileRecs)
                print('[DataSuper] Saving Result: {}'.format(result), file=sys.stderr)
                try:
                    result.save()
                except ds.database.RecordExistsError as ree:
                    print('[DataSuper] Record already exists: {}'.format(ree), file=sys.stderr)

                try:
                    groupName = params.groupName
                except KeyError:
                    groupName = None
                if groupName and (groupName.lower() != 'none'):
                    sgroup = dsrepo.db.sampleGroupTable.get(groupName)
                    sgroup.addResult(params.dsResultName)
                    sgroup.save(modify=True)

                outStr = ' '.join(output)
                shell('touch '+outStr)

            '''
        ruleBldr.setRun(runStr)

        return str(ruleBldr)

    def makeRegisterRule(self):
        '''
        every result in ModuleUltra gets checked into data
        super for tracking. This is essentially boilerplate code
        which is entirely determined by the module.

        This is a little awkward but this function actually
        generates the string to make the snakemake rule that
        registers the result. This is added to the pipeline
        definition at runtime.

        N.B. The result_name variable that snakemake has access to
        is not the same as the datasuper result_name. In practice it
        is probably the same as the datasuper sample_name. This is
        hacky but this whole approach is hacky.
        '''
        if self.level == 'SAMPLE':
            return self._makeSampleLevelRegisterRule()
        elif self.level == 'GROUP':
            return self._makeGroupLevelRegisterRule()

    def preprocessSnakemake(self):
        '''
        Every result schema preprocesses its own snakefile
        and returns it as a string

        Adds a register rule
        '''
        snakefileStr = open(self.snakeFilepath).read()
        if self.isOrigin():
            snakefileStr = self.editOrigins(snakefileStr)
        snakefileStr += self.makeRegisterRule()
        return snakefileStr

    def isOrigin(self):
        return self.origin

    def _makeFilePattern(self, fname, ext):
        if self.level == 'SAMPLE':
            fpat = '{{sample_name}}.{}.{}.{}'.format(self.module, fname, ext)
        elif self.level == 'GROUP':
            fpat = '{{group_name}}.{}.{}.{}'.format(self.module, fname, ext)
        return fpat

    def editOrigins(self, snakefileStr):
        return snakefileStr

    def preprocessConf(self, conf):
        dsRepo = ds.Repo.loadRepo()
        for fname, ftype in self.files.items():
            ext = dsRepo.getFileTypeExt(ftype)
            if self.isOrigin():
                fpattern = ""
            else:
                fpattern = self._makeFilePattern(fname, ext)
            try:
                conf[self.module][fname] = fpattern
            except KeyError:
                conf[self.module] = {fname: fpattern}
        return conf

    def getOutputFilePattern(self):
        return self._makeFilePattern('flag', 'registered')
