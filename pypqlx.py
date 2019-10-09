from __future__ import print_function, division
import sys
import datetime
from datetime import timezone
import records

class E(Exception):
    pass

def LOG(msg, end = "\n"):
    print(msg, file = sys.stderr, end = end)

def pdate(strdate):
    if isinstance(strdate, datetime.datetime):
        strdate.replace(tzinfo=timezone.utc)
        return strdate
    
    if len(strdate) == 10:
        d = datetime.datetime.strptime(strdate,  '%Y-%m-%d')
    else:
        d = datetime.datetime.strptime(strdate,  '%Y-%m-%d %H:%M:%S')
    d.replace(tzinfo=timezone.utc)
    return d
    
class PQLXdb(object):
    def __init__(self, user, password, machine, basedb):
        LOG("Opening Databases ... ", end = "")
        self.idx   = records.Database('mysql://%s:%s@%s/%s' % (user, password, machine, basedb))
        self.data  = records.Database('mysql://%s:%s@%s/%sDATA' % (user, password, machine, basedb))
        self.stats = records.Database('mysql://%s:%s@%s/%sSTATS' % (user, password, machine, basedb))
        
        self.idx.query('SET time_zone = "+0:00"')
        self.data.query('SET time_zone = "+0:00"')
        self.stats.query('SET time_zone = "+0:00"')
        
        LOG("Done.")
    
    def PDF(self, s, e, N, S, C, L = '', filters = None):
        if L == '': L = '--'
        s = pdate(s)
        e = pdate(e)
        LOG('From %s to %s' % (s,e))
        
        ID = self.nslcID(N, S, C, L)
        PSDIndex = "psd{}idx".format(ID)
        PSDTable = "psd{}".format(ID)
        sqlct = 'SELECT count(distinct(p1.psd_pk)) as N from {} p, {} p1 WHERE p1.psd_pk = p.psd_fk and UNIX_TIMESTAMP(TIMESTAMP(day,startT)) BETWEEN :s and :e'.format(PSDTable, PSDIndex)
        sqldt = 'SELECT YEAR(min(p1.day)) as Y1, DAYOFYEAR(min(p1.day)) as J1, YEAR(max(p1.day)) as Y2, DAYOFYEAR(max(p1.day)) as J2 from {} p, {} p1 WHERE p1.psd_pk = p.psd_fk and UNIX_TIMESTAMP(TIMESTAMP(day,startT)) BETWEEN :s and :e'.format(PSDTable, PSDIndex)
        sql   = 'SELECT period, power, count(*) as count FROM {} p, {} p1 WHERE p1.psd_pk = p.psd_fk and UNIX_TIMESTAMP(TIMESTAMP(day,startT)) BETWEEN :s and :e GROUP BY p.period, p.power ORDER BY p.period, p.power desc'.format(PSDTable, PSDIndex)
        
        r = self.data.query(sqlct, s = s.timestamp(), e = e.timestamp(), fetchall = True)
        nct =  r.one().N
        r = self.data.query(sqldt, s = s.timestamp(), e = e.timestamp(), fetchall = True)
        r = r.one()
        print(N, S, L, C, r.Y1, r.J1, r.Y2, r.J2, nct)
        
        r = self.data.query(sql, s = s.timestamp(), e = e.timestamp())
        for d in r: print("%.4f\t%d\t%d" % (d.period, d.power, d.count))
    
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
        # ~ r = db.nslcID('XC', 'VACA', 'HHZ')
        r = db.PDF('2017-12-01','2017-12-09 23:59:00', 'XC', 'VACA', 'HHZ')
        pass
    except E as e:
        LOG("Errors found:")
        LOG(" E:> " + str(e))
    db.close()
