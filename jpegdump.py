#!/usr/bin/python2

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

def parsestartofimage(data):
	print "SOI"

	return data

def parseappsegment(data, marker):
	app = marker - 0xffe0
	print "APP%d" % app

	(data, Lp) = parse16(data)
	print "APP%d.Lp = %d" % (app, Lp)

	data = skip(data, Lp - 2)

	return data

def parsedefinequantizationtables(data):
	print "DQT"

	(data, Lq) = parse16(data)
	print "DQT.Lq = %d" % Lq

	(data, PqTq) = parse8(data)
	Pq = (PqTq >> 4) & 0xf
	Tq = (PqTq >> 0) & 0xf

	if Pq == 0:
		bits = 8
	elif Pq == 1:
		bits = 16
	else:
		raise Exception("Pq out of range (%d)" % Pq)

	print "DQT.Pq = %d (%d bits)" % (Pq, bits)
	print "DQT.Tq = %d" % Tq

	for k in range(64):
		if bits == 8:
			(data, Qk) = parse8(data)
		if bits == 16:
			(data, Qk) = parse16(data)
		#print "DQT.Q%d = %d" % (k, Qk)

	return data

def parsestartofframe(data, marker):
	frame = marker - 0xffc0
	if frame == 0:
		type = "Baseline DCT"
	elif frame == 1:
		type = "Extended sequential DCT"
	elif frame == 2:
		type = "Progressive DCT"
	elif frame == 3:
		type = "Lossless sequential"

	print "SOF%d (%s)" % (frame, type)

	(data, Lf) = parse16(data)
	print "SOF%d.Lf = %d" % (frame, Lf)

	(data, P) = parse8(data)
	print "SOF%d.P = %d" % (frame, P)

	(data, Y) = parse16(data)
	print "SOF%d.Y = %d" % (frame, Y)

	(data, X) = parse16(data)
	print "SOF%d.X = %d" % (frame, X)

	(data, Nf) = parse8(data)
	print "SOF%d.Nf = %d" % (frame, Nf)

	for i in range(Nf):
		(data, Ci) = parse8(data)
		print "SOF%d.C[%d].Ci = %d" % (frame, i, Ci)

		(data, HiVi) = parse8(data)
		Hi = (HiVi >> 4) & 0xf
		Vi = (HiVi >> 0) & 0xf

		print "SOF%d.C[%d].Hi = %d" % (frame, i, Hi)
		print "SOF%d.C[%d].Vi = %d" % (frame, i, Vi)

		(data, Tqi) = parse8(data)
		print "SOF%d.C[%d].Tqi = %d" % (frame, i, Tqi)
		

	return data

def parsedefinehuffmantable(data):
	print "DHT"

	(data, Lh) = parse16(data)
	print "DHT.Lh = %d" % Lh

	data = skip(data, Lh - 2)

	return data

def parsestartofscan(data):
	print "SOS %d" % len(data)

	hexdump(data, 100)

	(data, Ls) = parse16(data)
	print "SOS.Ls = %d" % Ls

	(data, Ns) = parse8(data)
	print "SOS.Ns = %d" % Ns

	for i in range(Ns):
		(data, Cs) = parse8(data)
		print "SOS.Cs%d = %d" % (i + 1, Cs)

		(data, TdTa) = parse8(data)
		Td = (TdTa >> 4) & 0xf
		Ta = (TdTa >> 0) & 0xf
		print "SOS.Td%d = %d" % (i + 1, Td)
		print "SOS.Ta%d = %d" % (i + 1, Ta)

	(data, Ss) = parse8(data)
	print "SOS.Ss = %d" % Ss

	(data, Se) = parse8(data)
	print "SOS.Se = %d" % Se

	(data, AhAl) = parse8(data)
	Ah = (AhAl >> 4) & 0xf
	Al = (AhAl >> 0) & 0xf
	print "SOS.Ah = %d" % Ah
	print "SOS.Al = %d" % Al

	return data

def parsemarker(data, done):
	(data, marker) = parse16(data)

	if marker >= 0xffc0 and marker <= 0xffc3:
		data = parsestartofframe(data, marker)
	elif marker == 0xffc4:
		data = parsedefinehuffmantable(data)
	elif marker == 0xffd8:
		data = parsestartofimage(data)
	elif marker == 0xffda:
		data = parsestartofscan(data)
	elif marker == 0xffdb:
		data = parsedefinequantizationtables(data)
	elif marker >= 0xffe0 and marker <= 0xffef:
		data = parseappsegment(data, marker)
	else:
		raise Exception("unknown marker 0x%04x with %d bytes left" % (marker, len(data)))

	return (data, done)

def parsemarkers(data):
	done = False

	while not done:
		(data, done) = parsemarker(data, done)

for path in sys.argv[1:]:
	with open(path, "rb") as f:
		data = f.read()

		data = parsemarkers(data)
		if len(data) != 0:
			raise Exception("extraneous %d bytes of data at end of file" % len(data))
