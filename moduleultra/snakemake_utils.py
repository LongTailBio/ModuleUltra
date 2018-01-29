import datasuper as ds


def inputsToAllRule(config):
    out = []
    for sampleName in config['samples'].keys():
        for pattern in config['patterns']['sample']:
            out.append(pattern.format(sample_name=sampleName))
    for groupName in config['groups'].keys():
        for pattern in config['patterns']['group']:
            out.append(pattern.format(group_name=groupName))
    return out


def getSample(resultFilename):
    return resultFilename.split('/')[-1].split('.')[0]


def getOriginResultFiles(config, resultType, fileType):
    '''
    N.B. This function returns another function!
    It does not return the filepath itself
    '''

    def getter(wcs):
        try:
            return config['origins'][resultType][wcs.sample_name][fileType]
        except AttributeError:
            return config['origins'][resultType][wcs.group_name][fileType]

    return getter


def expandGroup(*samplePatterns, names=False):
    '''
    N.B. This function returns another function!
    It does not return the filepaths themselves
    '''
    def getter(wcs):
        gname = wcs.group_name
        dsrepo = ds.Repo.loadRepo()
        group = dsrepo.db.sampleGroupTable.get(gname)

        patterns = []
        for sample in group.allSamples():
            for pattern in samplePatterns:
                p = pattern.format(sample_name=sample.name)
                if names:
                    patterns.append(sample.name)
                else:
                    patterns.append(p)
        return patterns

    return getter

