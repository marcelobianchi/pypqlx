#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function, division
import sys, datetime

if sys.version_info[0] < 3:
    print("\n ** Needs Python 3 to run. ** \n", file = sys.stderr)
    sys.exit(1)

import records
import numpy as np

#
## Methods
#

def LOG(msg, end = "\n"):
    '''Our message logging toolkit'''
    print(msg, file = sys.stderr, end = end)


def pdate(strdate):
    '''
    Convert from str to datetime. Returned object should be
    insensible to the computer timezone location. 
    '''
    
    if isinstance(strdate, datetime.datetime):
        strdate.replace(tzinfo = datetime.timezone.utc)
        return strdate
    
    d = datetime.datetime.strptime(strdate,  '%Y-%m-%d' if len(strdate) == 10 else '%Y-%m-%d %H:%M:%S')
    d.replace(tzinfo = datetime.timezone.utc)
    
    return d


def ptime(strtime):
    fmt = '%H:%M:%S'
    
    if len(strtime) == 5: fmt = '%H:%M'
    if len(strtime) == 2: fmt = '%H'
    t = datetime.datetime.strftime(strtime, fmt).time()
    
    return t

#
## Classes
#

class E(Exception):
    '''Our exception class'''
    pass


class PDF(object):
    '''
    Class to represent PDF data.
    It can give out raw data, or, interpolated data.
    Also can generate the format needed by PQLX build PNG command.
    '''
    def __init__(self, first, last, ndata, N, S, C, L = ''):
        self.first  = first
        self.last   = last
        self.ndata  = ndata
        self.period = None
        self.power  = None
        self.count  = None
        self.N = N
        self.S = S
        self.C = C
        self.L = L if L != "" else "--"
    
    def mode(self):
        mode = []
        for i in sorted(set(pdf.period)):
            a = pdf.power[max(pdf.count[pdf.period == i])]
            mode.append(a)
        return
        
    def median(self):
        median = []
        for i in sorted(set(pdf.period)):
            cc = np.cumsum(pdf.count[pdf.period == i])
            if cc[-1] % 2 == 0:  #par
                central = int(cc[-1] / 2)
                pos = cc[cc >= central][0]
                if abs(central - pos) >= 1:
                    a = pdf.power[pdf.period == i][cc == pos]
                else:
                    a = int((pdf.power[pdf.period == i][cc == pos] + 
                    pdf.power[pdf.period == i][cc > pos][0])/2)
            else:  # impar
                central = int((cc[-1] + 1) / 2) #ok
                pos = cc[cc >= central][0]
                a = pdf.power[pdf.period == i][cc == pos]
            median.append(a) 
        return
    
    
    def average(self):
        avg = []
        for i in sorted(set(pdf.period)):
            a = sum(pdf.power[pdf.period == i] * pdf.count[pdf.period == i]) / sum(pdf.count[pdf.period == i])
            avg.append(a)
        return
    
    def min(self):
        minimun = []
        for i in sorted(set(pdf.period)):
            a = min(pdf.power[pdf.period == i])
            minimun.append(a)
        return
    
    def max(self):
        maximun =[]
        for i in sorted(set(pdf.period)):
            a = max(pdf.power[pdf.period == i])
            maximun.append(a)
        return
    
    def __str__(self):
        return "{}.{}.{}.{} :: {} - {} / Max Hit. {}".format(self.N,self.S,self.L,self.C, self.first, self.last, self.ndata)
    
    def fromrecords(self, data):
        '''
        Import data from a `records` query with fields:
            period, power and count.
        '''
        period = []
        power  = []
        count  = []
        
        for r in data:
            period.append(r.period)
            power.append(r.power)
            count.append(r.count)
        
        self.period = np.array(period)
        self.power  = np.array(power)
        self.count  = np.array(count)
        
        return
    
    def PNG(self, where = sys.stdout):
        '''
        Generate the output as needed for the PQLX make png command
        '''
        first = pdate(self.first)
        last  = pdate(self.last)
        print("{} {} {} {} {} {} {}".format(self.N, self.S, self.L, self.C,
                                            first.strftime("%Y %j"), last.strftime("%Y %j"), self.ndata), file = where)
        for pe, po, ct in zip(self.period, self.power, self.count):
            print("{:.6f}\t{}\t{}".format(pe,po,ct), file = where)
        return


class PQLXdb(object):
    '''
    A PQLXdb Database Interface Class:

    This class connects to a MySQL DB and tries to hook to a PQLX
    database. While doing that, it keep open connects to three databses
    associated to the PQLX main DB, the stats, index and data DBs.

    user     :: is a string username to connect to the mysql
    password :: is a string password to connect to the mysql
    machine  :: is a string machine where the mysql server listens
    basedb   :: is the PQLX database base name. Like configured in your server
    
    This class Implements:
    
    (1) A PDF method that returns PDF data between two dates and optionally
    filtered by some constraints.
    
    (2) An average PSD
    
    (3) PSDs
    '''
    def __init__(self, user, password, machine, basedb):
        #
        ## Opens needed connections to server
        #
        self.idx   = records.Database('mysql://%s:%s@%s/%s' % (user, password, machine, basedb))
        self.data  = records.Database('mysql://%s:%s@%s/%sDATA' % (user, password, machine, basedb))
        self.stats = records.Database('mysql://%s:%s@%s/%sSTATS' % (user, password, machine, basedb))
        
        #
        ## Set Server connections to UTC
        #
        self.idx.query('SET time_zone = "+0:00"')
        self.data.query('SET time_zone = "+0:00"')
        self.stats.query('SET time_zone = "+0:00"')
    
    #
    ## Private
    #
    def __nslcID__(self, N, S, C, L = ''):
        if L == '': L = '--'
        
        #
        ## Query
        #
        sql = 'SELECT chni_pk FROM nslc WHERE ntw=:ntw and stn=:stn and chn=:chn and loc=:loc'
        r = self.idx.query(sql, ntw = N, stn = S, chn = C, loc = L, fetchall=True)
        if len(r) != 1: raise E("{}.{}.{}.{} :: Not found in PQLx DB.".format(N,S,L,C))
        
        return r.one().chni_pk

    def __isOpen__(self):
        return self.idx.open
    
    def __PDF_filters__(self):
        pass

    #
    ## Public
    #
    def N_PDF(self, s, e, N, S, C, L = '', NS = 1, filters = None):
        s = pdate(s)
        e = pdate(e)
        
        if L == '': L = '--'
        pdfs = []
        
        if NS == 1:
            pdfs.append(self.PDF(s, e, N, S, C, L, filters))
            return pdfs

        step = (e - s) / NS
        for i in range(NS):
            pdfs.append(self.PDF(s + i * step, s + (i+1)*step, N, S, C, L, filters))
            
        return pdfs
    
    def PDF(self, s, e, N, S, C, L = '', filters = None):
        if not self.__isOpen__(): raise E("Cannot make any queries - not connected to server anymore")
        s = pdate(s)
        e = pdate(e)
        
        if L == '': L = '--'
        
        #
        ## Get psd_pk and setup tables & query helpers
        #
        ID = self.__nslcID__(N, S, C, L)
        
        PSDIndex = "psd{}idx".format(ID)
        PSDTable = "psd{}".format(ID)
        
        tables = 'FROM {} p, {} p1 WHERE p1.psd_pk = p.psd_fk'.format(PSDTable, PSDIndex)
        
        # This considers overlaps
        timec  = 'UNIX_TIMESTAMP(TIMESTAMP(day,startT)) < :e and UNIX_TIMESTAMP(TIMESTAMP(day,endT)) > :s '
        # in favor of an independent way of looking at time series
        # timec  = 'UNIX_TIMESTAMP(TIMESTAMP(day,startT)) BETWEEN :s and :e'
        
        #
        ## Query Number of PSDs available in query and First / Last PSD Dates
        #
        sql = 'SELECT count(distinct(p1.psd_pk)) as N {} and {}'.format(tables, timec)
        r = self.data.query(sql, s = s.timestamp(), e = e.timestamp(), fetchall = True)
        nct =  r.one().N
        
        sql = 'SELECT min(TIMESTAMP(day,startT)) as first, max(TIMESTAMP(day,startT)) as last {} and {}'.format(tables, timec)
        r = self.data.query(sql, s = s.timestamp(), e = e.timestamp(), fetchall = True)
        r = r.one()
        
        pdf = PDF(r.first, r.last, nct, N, S, C, L)
        
        #
        ## Query and compute PDF
        #
        sql   = 'SELECT period, power, count(*) as count {} and {} GROUP BY p.period, p.power ORDER BY p.period, p.power desc'.format(tables, timec)
        r = self.data.query(sql, s = s.timestamp(), e = e.timestamp())
        pdf.fromrecords(r)
        
        return pdf
    
    def close(self):
        '''
        Close connections to all databases
        '''
        if self.idx.open:   self.idx.close()
        if self.data.open:  self.data.close()
        if self.stats.open: self.stats.close()

#
## Main Code
#
if __name__ == "__main__":
    db = PQLXdb(user     = sys.argv[1],
                password = sys.argv[2],
                machine  = sys.argv[3],
                basedb   = sys.argv[4])
    
    filters = {
        'minhour' : '08:00:00',
        'maxhour' : None,
        'dow'     : ('Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa')
    }
    
    try:
        pdf  = db.PDF('2017-12-01','2017-12-09 23:59:00', 'XC', 'VACA', 'HHZ')
        pdfs = db.N_PDF('2017-12-01','2017-12-09 23:59:00', 'XC', 'VACA', 'HHZ', NS = 5)
        print(pdf)
        print("")
        for pdf in pdfs:
            print(pdf)
        # ~ pdf.PNG()
    except E as e:
        LOG("Errors found:")
        LOG(" E:> " + str(e))
    
    db.close()
