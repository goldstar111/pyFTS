import numpy as np
from pyFTS.common import FLR, fts
from pyFTS.models.nonstationary import common, flrg


class ConventionalNonStationaryFLRG(flrg.NonStationaryFLRG):
    """First Order NonStationary Fuzzy Logical Relationship Group"""

    def __init__(self, LHS, **kwargs):
        super(ConventionalNonStationaryFLRG, self).__init__(1, **kwargs)
        self.LHS = LHS
        self.RHS = set()

    def get_key(self):
        return self.LHS.name

    def append_rhs(self, c, **kwargs):
        self.RHS.add(c)

    def __str__(self):
        tmp = self.LHS.name + " -> "
        tmp2 = ""
        for c in sorted(self.RHS, key=lambda s: s.name):
            if len(tmp2) > 0:
                tmp2 = tmp2 + ","
            tmp2 = tmp2 + c.name
        return tmp + tmp2


class NonStationaryFTS(fts.FTS):
    """NonStationaryFTS Fuzzy Time Series"""
    def __init__(self, name, **kwargs):
        super(NonStationaryFTS, self).__init__(1, "NSFTS " + name, **kwargs)
        self.name = "Non Stationary FTS"
        self.detail = ""
        self.flrgs = {}

    def generate_flrg(self, flrs, **kwargs):
        for flr in flrs:
            if flr.LHS.name in self.flrgs:
                self.flrgs[flr.LHS.name].append_rhs(flr.RHS)
            else:
                self.flrgs[flr.LHS.name] = ConventionalNonStationaryFLRG(flr.LHS)
                self.flrgs[flr.LHS.name].append_rhs(flr.RHS)

    def train(self, data, **kwargs):

        window_size = kwargs.get('parameters', 1)
        tmpdata = common.fuzzySeries(data, self.sets, self.partitioner.ordered_sets,
                                     window_size, method='fuzzy')
        flrs = FLR.generate_recurrent_flrs(tmpdata)
        self.generate_flrg(flrs)

    def forecast(self, ndata, **kwargs):

        time_displacement = kwargs.get("time_displacement",0)

        window_size = kwargs.get("window_size", 1)

        l = len(ndata)

        ret = []

        for k in np.arange(0, l):

            tdisp = common.window_index(k + time_displacement, window_size)

            affected_sets = [ [self.sets[key], self.sets[key].membership(ndata[k], tdisp)]
                              for key in self.partitioner.ordered_sets
                              if self.sets[key].membership(ndata[k], tdisp) > 0.0]

            if len(affected_sets) == 0:
                affected_sets.append([common.check_bounds(ndata[k], self.partitioner, tdisp), 1.0])

            tmp = []

            if len(affected_sets) == 1:
                aset = affected_sets[0][0]
                if aset.name in self.flrgs:
                    tmp.append(self.flrgs[aset.name].get_midpoint(tdisp))
                else:
                    tmp.append(aset.get_midpoint(tdisp))
            else:
                for aset in affected_sets:
                    if aset[0].name in self.flrgs:
                        tmp.append(self.flrgs[aset[0].name].get_midpoint(tdisp) * aset[1])
                    else:
                        tmp.append(aset[0].get_midpoint(tdisp) * aset[1])

            pto = sum(tmp)

            #print(pto)

            ret.append(pto)

        return ret

    def forecast_interval(self, ndata, **kwargs):

        time_displacement = kwargs.get("time_displacement", 0)

        window_size = kwargs.get("window_size", 1)

        l = len(ndata)

        ret = []

        for k in np.arange(0, l):

            # print("input: " + str(ndata[k]))

            tdisp = common.window_index(k + time_displacement, window_size)

            affected_sets = [[self.sets[key], self.sets[key].membership(ndata[k], tdisp)]
                             for key in self.partitioner.ordered_sets
                             if self.sets[key].membership(ndata[k], tdisp) > 0.0]

            if len(affected_sets) == 0:
                affected_sets.append([common.check_bounds(ndata[k], self.partitioner, tdisp), 1.0])

            upper = []
            lower = []

            if len(affected_sets) == 1:
                aset = affected_sets[0][0]
                if aset.name in self.flrgs:
                    lower.append(self.flrgs[aset.name].get_lower(tdisp))
                    upper.append(self.flrgs[aset.name].get_upper(tdisp))
                else:
                    lower.append(aset.get_lower(tdisp))
                    upper.append(aset.get_upper(tdisp))
            else:
                for aset in affected_sets:
                    if aset[0].name in self.flrgs:
                        lower.append(self.flrgs[aset[0].name].get_lower(tdisp) * aset[1])
                        upper.append(self.flrgs[aset[0].name].get_upper(tdisp) * aset[1])
                    else:
                        lower.append(aset[0].get_lower(tdisp) * aset[1])
                        upper.append(aset[0].get_upper(tdisp) * aset[1])


            ret.append([sum(lower), sum(upper)])

        return ret