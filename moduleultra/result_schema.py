from .utils import getOrDefault

class ResultSchema:

    def __init__(self,  muRepo, pipeName, pipeVersion, schema):
        self.muRepo = muRepo
        self.muConfig = self.muRepo.muConfig
        self.pipelineName = pipeName
        self.pipelineVersion = pipeVersion
        
        self.name = schema['NAME']
        self.dependencies = getOrDefault( schema, 'DEPENDENCIES', [])
        self.module = getOrDefault( schema, 'MODULE', self.name)
        self.level = getOrDefault( schema, 'LEVEL', 'RESULT')

        self.snakeFilename = '{}.snkmk'.format(self.module)
        self.snakeFilepath = self.muConfig.getSnakefile(self.pipelineName,
                                                        self.pipelineVersion,
                                                        self.snakeFilename)
        self.files = {}
        files = schema['FILES']
        if type(files) == []:
            self.files = { str(i) : f for i, f in enumerate(files)}
        else:
            self.files = files    

            
    def makeRegisterRule(self):
        '''
        every result in ModuleUltra gets checked into data
        super for tracking. This is essentially boilerplate code
        which is entirely determined by the module.

        This is a little awkward but this function actually
        generates the string to make the snakemake rule that 
        registers the result. This is added to the pipeline
        definition at runtime.
        '''

        pass

    def preprocessSnakemake(self):
        '''
        Every result schema preprocesses its own snakefile 
        and returns it as a string

        Adds a register rule
        '''
        pass
