#!/usr/bin/python2

import struct, sys, os

def remaining(f):
    pos = f.tell()
    f.seek(0, os.SEEK_END)
    end = f.tell()
    f.seek(pos, os.SEEK_SET)
    return end - pos

def ateof(f):
    return remaining(f) == 0

def readbyte(f):
    if remaining(f) < 1:
        raise Exception('less than one byte left')
    b = struct.unpack_from("B", f.read(1))
    return b[0]

def readshort(f):
    if remaining(f) < 2:
        raise Exception('less than one short left')
    i = struct.unpack_from(">H", f.read(2))
    return i[0]

def readint(f):
    if remaining(f) < 4:
        raise Exception('less than one int left')
    i = struct.unpack_from(">I", f.read(4))
    return i[0]

def parseheader(f):
    ident = readint(f)
    if ident != 0x974a4232:
        f.seek(0, os.SEEK_SET)
        return True

    f.seek(0, os.SEEK_SET)
    ident = []
    for i in range(8):
        ident.append(readbyte(f))
    print "identifier: [" % ident,
    for e in ident:
        print "0x%x" % e,
    print "]"

    flags = readbyte(f)
    print "flags: %u" % flags
    sequential = (flags & 1) == 1

    pages = readint(f)
    print "pages: %u" % pages

    return sequential

def parsesegment(f, sequential):
    print "Parsing new segment at %u" % f.tell()

    nbr = readint(f);
    print "segment number: %u (0x%08x)" % (nbr, nbr)

    flags = readbyte(f);
    print "\tsegment header flags: 0x%02x" % flags
    
    deferred = (flags >> 7) & 1
    print "\t\tdeferred non-retain: %u" % deferred

    assocation = (flags >> 6) & 1
    print "\t\tpage assocation size: %u" % assocation

    typ = flags & 0x3f
    if typ == 0:
        s = "symbol dictionary"
    elif typ == 4:
        s = "intermediate text region"
    elif typ == 6:
        s = "immediate text region"
    elif typ == 7:
        s = "immediate lossless text region"
    elif typ == 16:
        s = "pattern dictionary"
    elif typ == 22:
        s = "immediate halftone region"
    elif typ == 23:
        s = "immediate lossless halftone region"
    elif typ == 38:
        s = "immediate generic region"
    elif typ == 39:
        s = "immediate loessless generic region"
    elif typ == 42:
        s = "immediate generic refinement region"
    elif typ == 48:
        s = "page information"
    elif typ == 49:
        s = "end of page"
    elif typ == 50:
        s = "end of stripe"
    elif typ == 51:
        s = "end of file"
    elif typ == 54:
        s = "colour palette"
    elif typ == 62:
        s = "extension"
    else:
        s = "UNKNOWN"
    print "\t\tsegment type: %s (%d)" % (s, typ)

    referrals = readbyte(f)
    segments = (referrals >> 5) & 0x7
    if segments == 7:
        referrals = (referrals << 8) | readbyte(f)
        referrals = (referrals << 8) | readbyte(f)
        referrals = (referrals << 8) | readbyte(f)
        print "\treferrals: 0x%08x" % referrals

        print "\t\tlong form indicator: 0x%01x" % segments

        segments = referrals & 0x1fffffff
        print "\t\tsegments: %u" % segments

        rts = (segments + 1) / 8
        if (segments + 1) % 8:
            rts = rts + 1

        retain = []
        for j in range(rts):
            rt = readbyte(f)
            for i in range(8):
                retain.append((rt >> i) & 1)
        print "\t\tretain: %s" % retain
    else:
        print "\treferrals: 0x%02x" % referrals
        print "\t\tsegments: %u" % segments

	if segments == 5 or segments == 6:
		print "\t\tinvalid number of segments!"

        retain = []
        for i in range(5):
            retain.append((referrals >> i) & 1)
        print "\t\tretain: %s" % retain

    refs = []
    for i in range(segments):
        if nbr <= 256:
            refs.append(readbyte(f))
        else:
            refs.append(readshort(f))
    print"\t\t%s" % refs

    if assocation == 0:
        page = readbyte(f)
    else:
        page = readint(f)
    print "\tpage association: %u" % page

    length = readint(f)
    if length == 0xffffffff:
        print "\tlength: ?"
    else:
        print "\tlength: %u" % length

    if sequential:
        f.read(length)

    if typ == 51:
        print "End of segments at %u" % (f.tell() - 1)

    return typ == 51

for fn in sys.argv[1:]:
    print "Processing %s" % fn
    f = open(fn)
    try:
        sequential = parseheader(f)
        eod = False
        while not ateof(f) and not eod:
            eod = parsesegment(f, sequential)
        f.close()
    except Exception as error:
        print "Caught exception: %s" % error
