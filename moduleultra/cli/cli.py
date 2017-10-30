import click
import sys
from moduleultra import *

@click.group()
def main():
    pass

@main.command()
def init():
    try:
        ModuleUltraConfig.initConfig()
    except ModuleUltraConfigAlreadyExists:
        pass # this is fine
    
    try:
        ModuleUltraRepo.initRepo()
    except ModuleUltraRepoAlreadyExists:
        print('Repo already exists.', file=sys.stderr)

################################################################################
        
@main.group()
def add():
    pass

@add.command(name='pipeline')
@click.option('-v' ,'--version', default=None, type=str)
@click.option('--modify/--no-modify', default=False)
@click.argument('name', nargs=1)
def addPipeline( version, modify, name):
    repo = ModuleUltraRepo.loadRepo()
    try:
        repo.addPipeline(name, version=version, modify=modify)
    except errors.PipelineAlreadyInRepoError:
        print('{} is already in this repo.'.format(name), file=sys.stderr)

################################################################################

@main.command(name='install')
@click.option('--dev/--normal', default=False)
@click.argument('uri', nargs=1)
def installPipeline(uri, dev=False):
    muConfig = ModuleUltraConfig.load()
    muConfig.installPipeline(uri, dev=dev)

@main.command(name='uninstall')
@click.option('-v' ,'--version', default=None, type=str)
@click.argument('name', nargs=1)
def uninstallPipeline(name, version=None):
    muConfig = ModuleUltraConfig.load()
    muConfig.uninstallPipeline(name, version=version)

@main.command(name='reinstall')
@click.option('-v' ,'--version', default=None, type=str)
@click.option('--dev/--normal', default=False)
@click.argument('name', nargs=1)
@click.argument('uri', nargs=1)
def reinstallPipeline(name, uri, version=None, dev=False):
    muConfig = ModuleUltraConfig.load()
    muConfig.uninstallPipeline(name, version=version)
    muConfig.installPipeline(uri, dev=dev)

################################################################################

@main.command(name='run')
@click.option('-p', '--pipeline', default=None, type=str)
@click.option('-v' ,'--version', default=None, type=str)
@click.option('--endpts/--all-endpts' , default=False)
@click.option('--choose/--all' , default=False)
@click.option('--local/--cluster' , default=False)
@click.option('--dryrun/--wetrun' , default=False)
@click.option('--unlock/--no-unlock' , default=False)
@click.option('-j', '--jobs', default=1)
def runPipeline(pipeline, version, endpts, choose, local, dryrun, unlock, jobs):
    repo = ModuleUltraRepo.loadRepo()
    pipe = repo.getPipelineInstance(pipeline, version=version)
    dsRepo = repo.datasuperRepo()
    
    # select sets
    if endpts:
        endpts = UserMultiChoice('What end points should be evaluated?',
                                 pipe.listEndpoints()).resolve()
    groups = None
    if choose and BoolUserInput('Process data from specific sample groups?', False).resolve():
        groups = UserMultiChoice('What sample groups should be processed?',
                                 dsRepo.db.sampleGroupTable.getAll(),
                                 display=lambda x: x.name).resolve()
    samples=None
    if choose and BoolUserInput('Process data from a specific samples?', False).resolve():
        if groups is None:
            samplesToChooseFrom = []
            for group in groups:
                samplesToChooseFrom += group.samples()
        else:
            samplesToChooseFrom = dsRepo.db.sampleTable.getAll()
        samples = UserMultiChoice('What samples should data be taken from?',
                                  samplesToChooseFrom,
                                  display=lambda x: x.name).resolve()
    
    # run the pipeline
    pipe.run(endpts=endpts, groups=groups, samples=samples,
             dryrun=dryrun, unlock=unlock, local=local, jobs=jobs)
    
    
################################################################################

@main.group(name='view')
def view():
    pass

@view.command(name='pipelines')
@click.option('--globally/--local' , default=False)
def viewPipelines(globally):
    if globally:
        muConfig = ModuleUltraConfig.load()
        for pName, versions in muConfig.listInstalledPipelines().items():
            vs = ' '.join(versions)
            print('{} :: {}'.format(pName,vs))
    else:
        repo = ModuleUltraRepo.loadRepo()
        for pName in repo.listPipelines():
            print(pName)

################################################################################

@view.group(name='detail')
def detail():
    pass

@detail.command(name='pipeline')
@click.argument('name', nargs=1)
def detailPipeline(name):
    pass



if __name__ == '__main__':
    main()
