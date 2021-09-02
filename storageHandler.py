#!/usr/bin/env python3

import sqlite3

class StorageHandler(object):

    def __init__(self, filename):
        self.filename = filename
        self.conn = sqlite3.connect(filename)
        self.conn.row_factory = sqlite3.Row

        cur = self.conn.cursor()

        cur.execute('create table if not exists lastMod (loc text unique, lastmod text)')
        cur.execute('create table if not exists picHash (hash text unique, locationCount integer)')
        self.conn.commit()
    

    def __del__(self):
        self.conn.close()

    def getLoc(self, loc):
        cur = self.conn.cursor()

        res = cur.execute('select * from lastMod where loc=?',(loc,)).fetchall()
        cur.close()
        return res

    def getAllLoc(self):
        cur = self.conn.cursor()

        res = cur.execute('select * from lastMod').fetchall()
        cur.close()
        return res

    def upsertLoc(self, loc, lastmod):
        cur = self.conn.cursor()

        cur.execute('INSERT OR REPLACE INTO lastmod (loc, lastmod) VALUES (? , ?)',(loc,lastmod))
        self.conn.commit()
        cur.close()

        return

    def getHash(self, h):
        cur = self.conn.cursor()

        res = cur.execute('select * from picHash where hash=?',(h,)).fetchall()
        cur.close()
        return res

    def upsertHash(self, h, location):
        cur = self.conn.cursor()

        cur.execute('INSERT OR REPLACE INTO picHash (hash, locationCount) VALUES (? , ?)',(h,location))
        self.conn.commit()
        cur.close()

        return

    def __toDict(self,l):
        d = dict()
        for k,v in l:
            d[k] = v
        print(d)
        return d;


#if __name__ == '__main__':
#    ph = StorageHandler('test.db')
#    ph.upsertHash('1234',1)
#    ph.upsertHash('1234',1)
#    print(dict(ph.getHash('1234')))
#    del ph
