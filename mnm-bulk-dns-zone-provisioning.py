#!/usr/bin/env python3
# Copyright (C) 2013 Men & Mice
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND MEN & MICE DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL MEN & MICE BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
# OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

"""
This script supports bulk additions and removals of DNS resource
records from a file.

The input file can have two different formats:

Format one for deletions. Each line is a new entry. The first column
is the zonefile, the second column is the DNS domainname (ownername)
to be removed. All records that are owned by the domainname are removed:

84.151.10.in-addr.arpa. 244
84.151.10.in-addr.arpa. 242
84.151.10.in-addr.arpa. 130
21.10.in-addr.arpa.         41.127
21.10.in-addr.arpa.         154.127
21.10.in-addr.arpa.         155.127
21.10.in-addr.arpa.         35.127

The second format can be used for deletions and additions. The first
two columns are again the zonename and the ownername. Field three is
the record type, field four is the record data (can be multiple fields
separated by whitespace).

84.151.10.in-addr.arpa. 244 PTR www.example.com.
84.151.10.in-addr.arpa. 242 PTR mail.example.net.
84.151.10.in-addr.arpa. 130 PTR ldap.example.org.
example.com.  www  A 192.0.2.80
example.com.  @    NS  ns1.example.com.
example.net.  @    mx 10 mail.example.com.

The column fields are separated by whitespace.

This script requires the Men & Mice Suite CLI mmcmd

Author: Carsten Strotmann - carsten@menandmice.com
Version: 0.1
Date: 2013-08-28
"""

import os
import sys
import subprocess
import string
from optparse import OptionParser

server   = "127.0.0.1"
mmcmdpgm = "/usr/bin/mmcmd"
user     = "administrator"
password = "menandmice"
masterserver = "ns1.example.com"

def mmcmd(cmd, debugflag=False):
    if debugflag: 
        print("mmcmd {}".format(cmd))
    output = subprocess.check_output([mmcmdpgm, 
                                      "-q", "-s{}".format(server), 
                                      "-u{}".format(user), 
                                      "-p{}".format(password), 
                                      "{}; quit;".format(cmd)], timeout=60).decode("utf8")
    return output.rstrip("\n")


# Main program
if __name__ == "__main__":
    parser = OptionParser(usage="Usage: %prog [--help | options] file")
    parser.add_option("-d", action="store_true", dest="debugflag",
                      default=False, help="print debug information")
    parser.add_option("-r", action="store_true", dest="removeflag",
                      default=False, 
                      help="remove records instead of adding them")
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error(
            "you must supply the name of the control file containing the records")

    infile  = args[0].lower()
    f = open(infile,'r')

    print ("Reading from control file [{}]".format(infile))
    linenum = 0

    for l in f:
        linenum = linenum + 1
        l = l.rstrip("\n")
        fields = l.split(maxsplit=4)
        if len(fields) < 2:
            continue
        # ------------------------------------
        # remove records
        # ------------------------------------
        if options.removeflag:
            zone = ""
            owner = ""
            rtype = ""
            rdata = ""
            if (len(fields) == 2):
                zone, owner  = fields[0], fields[1]
            else:
                if (len(fields) > 3):
                    zone, owner, rtype, rdata  = fields[0], fields[1],fields[2], " ".join(fields[3:])
                else:
                    continue
            # make zone fully qualified        
            if not zone.endswith("."):
                zone = zone + "."
                # create the fqdn (Full Qualified Domain Name) ownername
            if not owner.endswith("@"):
                if owner.endswith("."):
                    fqdn = owner + zone
                else:
                    fqdn = owner + "." + zone
            else:
                fqdn = zone

            if options.debugflag:
                print(rr)
            zones = mmcmd("zones", options.debugflag)
            zones = zones.splitlines()
            zonelist = [z.split(" ",1)[0] for z in zones]
            # cannot remove records from non-existing zone
            if zone in zonelist:
                print("Searching in zone [{}] ...".format(zone))
                records = mmcmd("print -l {}".format(zone))
                records = records.splitlines()
                records = [r.split("\t",4) for r in records]

                for r in records:
                    zowner, zttl, znetclass, zrtype, zrdata = r[0], r[1], r[2], r[3], r[4]
                    zrdata = " ".join(zrdata.split())
                    idx, zowner = zowner.split(":")
                    idx = idx.strip()
                    zowner = zowner.strip()
                    if zowner.endswith("@"):
                        zowner = zone
                    if owner.endswith("@"):
                        owner = zone
                    rr = " ".join([zowner, zrtype, zrdata])
                    # test if record should be removed
                    remove = False
                    if zowner == owner:
                        remove = True
                    if not rtype == "":
                        if not zrtype == rtype:
                            remove = False
                    if not rdata == "":
                        if not zrdata == rdata:
                            remove = False
                    if remove:
                        print("Removing [{}] ...".format(rr))
                        rc = mmcmd("del {} {}; save {}".format(zone,
                                                               idx, zone))
                        if (len(rc)>0):
                            print("Error from mmcmd: {}".format(rc))                        
            else:
                print("Cannot remove records from non-existing zone [{}]".format(zone))


        # ------------------------------------
        # add records
        # ------------------------------------
        else:
            if (len(fields) < 4):
                print("Not enough fields for record addition, ignoring line" +
                      " {} (expected 4, got {})".format(linenum, len(fields)))
            else:
                zone, owner, rtype, rdata  = fields[0], fields[1], fields[2], " ".join(fields[3:])
                # make zone fully qualified        
                if not zone.endswith("."):
                    zone = zone + "."
                    # create the fqdn (Full Qualified Domain Name) ownername
                if not owner.endswith("@"):
                    if owner.endswith("."):
                        fqdn = owner + zone
                    else:
                        fqdn = owner + "." + zone
                else:
                    fqdn = zone
                            
                rr = " ".join([fqdn, rtype, rdata])
                if options.debugflag:
                    print(rr)
                zones = mmcmd("zones", options.debugflag)
                zones = zones.splitlines()
                zonelist = [z.split(" ",1)[0] for z in zones]
                # add zone if the zone does not exist
                if not zone in zonelist:
                    print ("Creating zone [{}]".format(zone))
                    output = mmcmd("addzone {} {} *; save {}".format(zone,
                                                                     masterserver,
                                                                     zone ),
                                   options.debugflag)
                # add record
                print("Adding record [{}] to zone [{}]".format(rr, zone))
                rc = mmcmd("add {} -1 {}; save {}".format(zone, rr, zone),options.debugflag)
                if (len(rc)>0):
                    print("Error from mmcmd: {}".format(rc))

    print("Done. Processed {} lines".format(linenum))
