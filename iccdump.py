#!/usr/bin/python

import os
import sys
import struct

def hexdump(data, length):
	print "hexdump(%d):" % length,
	for i in range(length):
		print "%02x" % ord(data[i]),
	print "\n"

def skip(data, length):
	return data[length:]

def parse(data, length):
	if len(data) == 0:
		raise Exception("premature end in marker (expecting %d bytes, no bytes left)" % length)
	if len(data) < length:
		print("premature end in marker (expecting %d bytes, finding %d bytes), parsing what's available" % (length, len(data)))
		return ([], data)
	return (data[length:], data[0:length])

def parse8(data):
	(data, value) = parse(data, 1)
	value = ord(value)
	return (data, value)

def parse16(data):
	(data, value) = parse(data, 2)
	value  = struct.unpack(">H", value)[0] 
	return (data, value)

def parse32(data):
	(data, value) = parse(data, 4)
	value  = struct.unpack(">I", value)[0] 
	return (data, value)

def parsearray(data, length):
	s = ""
	for i in range(length):
		s = s + "%02x " % ord(data[i])
	s = "[" + s[:-1] + "]"
	return (data[length:], s)

def parsestring(data, length):
	s = ""
	for i in range(length):
		v = ord(data[i])
		if v < 32:
			continue
		s = s + chr(v)
	return (data[length:], s)

def parseheader(data):
        (data, size) = parse32(data)
        print "hdr.size = %d" % size

        (data, cmmtype) = parse32(data)
        print "hdr.cmmtype = %d" % cmmtype

        (data, major) = parse8(data)
        (data, minor) = parse8(data)
        (data, reserved) = parse16(data)
        print "hdr.version = %d.%02x" % (major, minor)
        print "hdr.reserved = %d" % (reserved)

        (data, clazz) = parsestring(data, 4)
        print "hdr.class = %s" % clazz

        (data, colorspace) = parsestring(data, 4)
        print "hdr.colorspace = %s" % colorspace

        (data, connectionspace) = parsestring(data, 4)
        print "hdr.connectionspace = %s" % connectionspace

        (data, year) = parse16(data)
        (data, month) = parse16(data)
        (data, day) = parse16(data)
        (data, hour) = parse16(data)
        (data, minute) = parse16(data)
        (data, second) = parse16(data)
        print "hdr.datetime = %04d-%02d-%02d %02d:%02d:%02d" % (year, month, day, hour, minute, second)

        (data, signature) = parsestring(data, 4)
        print "hdr.signature = %s" % signature

        (data, platformsignature) = parsestring(data, 4)
        print "hdr.platformsignature = %s" % platformsignature

        (data, flags) = parse32(data)
        print "hdr.flags = 0x%08x" % flags

        (data, manufacturer) = parsestring(data, 4)
        print "hdr.manufacturer = %s" % manufacturer

        (data, model) = parsestring(data, 4)
        print "hdr.model = %s" % model

        (data, flags) = parse32(data)
	reflectivetransparency = (flags >> 0) & 0x1
	glossymatte = (flags >> 1) & 0x1
	polarity = (flags >> 2) & 0x1
	media = (flags >> 3) & 0x1
        reserved = (flags >> 4) & 0xfffffff

        if reflectivetransparency == 0:
                print "hdr.reflective/transparency = reflective"
        elif reflectivetransparency == 1:
                print "hdr.reflective/transparency = transparency"
        else:
                print "hdr.reflective/transparency = %d" % reflectivetransparency
        if glossymatte == 0:
                print "hdr.glossy/matte = glossy"
        elif glossymatte == 1:
                print "hdr.glossy/matte = matte"
        else:
                print "hdr.glossy/matte = %d" % glossymatte
        if polarity == 0:
                print "hdr.polarity = positive"
        elif polarity == 1:
                print "hdr.polarity = negative"
        else:
                print "hdr.polarity = %d" % polarity
        if media == 0:
                print "hdr.media = color"
        elif media == 1:
                print "hdr.media = black & white"
        else:
                print "hdr.media = %d" % media
        print "hdr.reserved = %d" % reserved

        (data, unused) = parse32(data)
        print "hdr.unused = %d" % unused

        (data, intent) = parse32(data)
        if intent == 0:
                print "hdr.intent = perceptual"
        elif intent == 1:
                print "hdr.intent = media-relative colorimetric"
        elif intent == 2:
                print "hdr.intent = saturation"
        elif intent == 3:
                print "hdr.intent = icc-absolute colorimetric"
        else:
                print "hdr.intent = %d" % intent

        (data, x) = parse32(data)
        (data, y) = parse32(data)
        (data, z) = parse32(data)
        print "hdr.nciexyz = 0x%08x/0x%08x/0x%08x" % (x, y, z)

        (data, creator) = parsestring(data, 4)
        print "hdr.creator = %s" % creator

        (data, id) = parsearray(data, 16)
        print "hdr.id = %s" % id

        (data, reserved) = parsearray(data, 28)
        print "hdr.reserved = %s" % reserved

        return data

def parsemultilocalizedunicodetype(prefix, data):
        alldata = data

        (data, signature) = parsestring(data, 4)
        print "%s.signature = %s" % (prefix, signature)

        (data, reserved) = parse32(data)
        print "%s.reserved = 0x%08x" % (prefix, reserved)

        (data, records) = parse32(data)
        print "%s.records = %d" % (prefix, records)

        (data, size) = parse32(data)
        print "%s.size = %d" % (prefix, size)

        for i in range(records):
                (data, languagecode) = parsestring(data, 2)
                print "%s.record[%02d].languagecode = %s" % (prefix, i, languagecode)
                (data, countrycode) = parsestring(data, 2)
                print "%s.record[%02d].countrycode = %s" % (prefix, i, countrycode)
                (data, length) = parse32(data)
                print "%s.record[%02d].length = %d" % (prefix, i, length)
                (data, offset) = parse32(data)
                print "%s.record[%02d].offset = %d" % (prefix, i, offset)

                string = parsestring(alldata[offset:offset + length], length)
                print "%s.record[%02d].string = %s" % (prefix, i, string)

def parsexyztype(prefix, data):
        (data, signature) = parsestring(data, 4)
        print "%s.signature = %s" % (prefix, signature)

        (data, reserved) = parse32(data)
        print "%s.reserved = %d" % (prefix, reserved)

        for i in range(len(data) / 12):
                (data, x) = parse32(data)
                (data, y) = parse32(data)
                (data, z) = parse32(data)
                print "%s.value[%d].x = %d" % (prefix, i, x)
                print "%s.value[%d].y = %d" % (prefix, i, y)
                print "%s.value[%d].z = %d" % (prefix, i, z)

        if len(data) > 0:
                print "%s.trailing data" % prefix

def parses15fixed16arraytype(prefix, data):
        (data, signature) = parsestring(data, 4)
        print "%s.signature = %s" % (prefix, signature)

        (data, reserved) = parse32(data)
        print "%s.reserved = %d" % (prefix, reserved)

        for i in range(len(data) / 4):
                (data, x) = parse32(data)
                print "%s.value[%d] = %d" % (prefix, i, x)

        if len(data) > 0:
                print "%s.trailing data" % prefix

def parseparametriccurvetype(prefix, data):
        (data, signature) = parsestring(data, 4)
        print "%s.signature = %s" % (prefix, signature)

        (data, reserved) = parse32(data)
        print "%s.reserved = %d" % (prefix, reserved)

        (data, encodedvalue) = parse16(data)
        print "%s.encodedvalue = %d" % (prefix, encodedvalue)

        (data, reserved) = parse16(data)
        print "%s.reserved = %d" % (prefix, reserved)

        for i in range(len(data) / 4):
                (data, x) = parse32(data)
                print "%s.value[%d] = %d" % (prefix, i, x)

        if len(data) > 0:
                print "%s.trailing data" % prefix

def parsecurveorparametriccurvetype(prefix, data):
        (_, signature) = parsestring(data, 4)
        if signature == 'para':
                parseparametriccurvetype(prefix, data)
        else:
                print "Cannot parse type %s" % signature

def parsechromaticitytype(prefix, data):
        (data, signature) = parsestring(data, 4)
        print "%s.signature = %s" % (prefix, signature)

        (data, reserved) = parse32(data)
        print "%s.reserved = %d" % (prefix, reserved)

        (data, channels) = parse16(data)
        print "%s.channels = %d" % (prefix, channels)

        (data, encoded) = parse16(data)
        print "%s.encoded = %d" % (prefix, encoded)

        for i in range(channels):
                (data, coord) = parse32(data)
                print "%s.coord[%02d] = %d" % (prefix, i, coord)

def parsetag(tag, data):
        if tag == 'desc':
                parsemultilocalizedunicodetype("profiledescriptiontag", data)
        elif tag == 'cprt':
                parsemultilocalizedunicodetype("copyrighttag", data)
        elif tag == 'wtpt':
                parsexyztype("mediawhitepointtag", data)
        elif tag == 'chad':
                parses15fixed16arraytype("chromaticadaptiontag", data)
        elif tag == 'rXYZ':
                parsexyztype("redmatrixcolumntag", data)
        elif tag == 'bXYZ':
                parsexyztype("bluematrixcolumntag", data)
        elif tag == 'gXYZ':
                parsexyztype("greenmatrixcolumntag", data)
        elif tag == 'rTRC':
                parsecurveorparametriccurvetype("redtrctag", data)
        elif tag == 'gTRC':
                parsecurveorparametriccurvetype("greentrctag", data)
        elif tag == 'bTRC':
                parsecurveorparametriccurvetype("bluetrctag", data)
        elif tag == 'chrm':
                parsechromaticitytype("chromaticitytag", data)
        else:
                print "Cannot parse tag %s" % tag

def parsetags(data, alldata):
        (data, count) = parse32(data)
        print "tags.count = %d" % count

        for i in range(count):
                (data, sig) = parsestring(data, 4)
                (data, offset) = parse32(data)
                (data, size) = parse32(data)

                print "tag[%02d]: %s %d byte @%d" % (i, sig, size, offset)
                parsetag(sig, alldata[offset:offset + size])

        return data

for path in sys.argv[1:]:
	with open(path, "rb") as f:
		data = f.read()

                alldata = data

                data = parseheader(data)
                data = parsetags(data, alldata)
