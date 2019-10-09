from __future__ import print_function, division
import sys
import records

class E(Exception):
    pass

def LOG(msg, end = "\n"):
    print(msg, file = sys.stderr, end = end)

class PQLXdb(object):
    def __init__(self, user, password, machine, basedb):
        LOG("Opening Databases ... ", end = "")
        self.idx   = records.Database('mysql://%s:%s@%s/%s' % (user, password, machine, basedb))
        self.data  = records.Database('mysql://%s:%s@%s/%sDATA' % (user, password, machine, basedb))
        self.stats = records.Database('mysql://%s:%s@%s/%sSTATS' % (user, password, machine, basedb))
        LOG("Done.")
    
    def nslcID(self, N, S, C, L = ''):
        if L == '': L = '--'
        sql = 'SELECT chni_pk FROM nslc WHERE ntw=:ntw and stn=:stn and chn=:chn and loc=:loc'
        r = self.idx.query(sql, ntw = N, stn = S, chn = C, loc = L, fetchall=True)
        if len(r) != 1: raise E("{}.{}.{}.{} :: Not found in PQLx DB.".format(N,S,L,C))
        return r.one().chni_pk
    
    def close(self):
        LOG("Closing Databases ... ", end = "")
        if self.idx.open: self.idx.close()
        if self.data.open: self.data.close()
        if self.stats.open: self.stats.close()
        LOG("Done")

if __name__ == "__main__":
    db = PQLXdb(user = sys.argv[1], password = sys.argv[2], machine = sys.argv[3], basedb = sys.argv[4])

    try:
        r = db.nslcID('XC', 'VACA', 'HHZ')
        print(r)
    except E as e:
        LOG("Errors found:")
        LOG(" E:> " + str(e))
    db.close()
