#aigen.py
""" 
This is a library to generate AI files containing text and graphics.  It is
part of the Adobe Illustrator format backend for PIDDLE foundation for a
complete Reporting solution in Python.

(C) Copyright Bill Bedford 1999
parts (C) Copyright Andy Robinson 1998-1999
"""

import os
import sys
import string
import time
import tempfile
pass  # types wildcard removed


##############################################################
#
#                       Constants and declarations
#
##############################################################



StandardEnglishFonts = [
        'Courier', 'Courier-Bold', 'Courier-Oblique', 'Courier-BoldOblique',  
        'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique', 
        'Helvetica-BoldOblique',
        'Times-Roman', 'Times-Bold', 'Times-Italic', 'Times-BoldItalic',
        'Symbol','ZapfDingbats']

AIError = 'AIError'
AFMDIR = '.'

##############################################################
#
#                       AI Metrics
# This is a preamble to give us a stringWidth function.
# loads and caches AFM files, but won't need to as the
# standard fonts are there already
##############################################################

widths = {'courier': [
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
0,600,600,600,600,0,600,600,600,600,600,600,600,600,0,600,
0,600,600,600,600,600,600,600,600,0,600,600,0,600,600,600,
600,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,600,0,600,0,0,0,0,600,600,600,600,0,0,0,0,
0,600,0,0,0,600,0,0,600,600,600,600,0,0,600],
'courier-bold': [
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
0,600,600,600,600,0,600,600,600,600,600,600,600,600,0,600,
0,600,600,600,600,600,600,600,600,0,600,600,0,600,600,600,
600,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,600,0,600,0,0,0,0,600,600,600,600,0,0,0,0,
0,600,0,0,0,600,0,0,600,600,600,600,0,0,600],
'courier-boldoblique': [
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
0,600,600,600,600,0,600,600,600,600,600,600,600,600,0,600,
0,600,600,600,600,600,600,600,600,0,600,600,0,600,600,600,
600,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,600,0,600,0,0,0,0,600,600,600,600,0,0,0,0,
0,600,0,0,0,600,0,0,600,600,600,600,0,0,600],
'courier-oblique': [
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,600,600,600,600,600,600,600,600,600,600,600,600,600,600,600,
0,600,600,600,600,0,600,600,600,600,600,600,600,600,0,600,
0,600,600,600,600,600,600,600,600,0,600,600,0,600,600,600,
600,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,600,0,600,0,0,0,0,600,600,600,600,0,0,0,0,
0,600,0,0,0,600,0,0,600,600,600,600,0,0,600],
'helvetica': [
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
278,278,355,556,556,889,667,222,333,333,389,584,278,333,278,278,
556,556,556,556,556,556,556,556,556,556,278,278,584,584,584,556,
1015,667,667,722,722,667,611,778,722,278,500,667,556,833,722,778,
667,778,722,667,611,722,667,944,667,667,611,278,278,278,469,556,
222,556,556,500,556,556,278,556,556,222,222,500,222,833,556,556,
556,556,333,500,278,556,500,722,500,500,500,334,260,334,584,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,333,556,556,167,556,556,556,556,191,333,556,333,333,500,500,
0,556,556,556,278,0,537,350,222,333,333,556,1000,1000,0,611,
0,333,333,333,333,333,333,333,333,0,333,333,0,333,333,333,
1000,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,1000,0,370,0,0,0,0,556,778,1000,365,0,0,0,0,
0,889,0,0,0,278,0,0,222,611,944,611,0,0,834],
'helvetica-bold': [
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
278,333,474,556,556,889,722,278,333,333,389,584,278,333,278,278,
556,556,556,556,556,556,556,556,556,556,333,333,584,584,584,611,
975,722,722,722,722,667,611,778,722,278,556,722,611,833,722,778,
667,778,722,667,611,722,667,944,667,667,611,333,278,333,584,556,
278,556,611,556,611,556,333,611,611,278,278,556,278,889,611,611,
611,611,389,556,333,611,556,778,556,556,500,389,280,389,584,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,333,556,556,167,556,556,556,556,238,500,556,333,333,611,611,
0,556,556,556,278,0,556,350,278,500,500,556,1000,1000,0,611,
0,333,333,333,333,333,333,333,333,0,333,333,0,333,333,333,
1000,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,1000,0,370,0,0,0,0,611,778,1000,365,0,0,0,0,
0,889,0,0,0,278,0,0,278,611,944,611,0,0,834],
'helvetica-boldoblique': [
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
278,333,474,556,556,889,722,278,333,333,389,584,278,333,278,278,
556,556,556,556,556,556,556,556,556,556,333,333,584,584,584,611,
975,722,722,722,722,667,611,778,722,278,556,722,611,833,722,778,
667,778,722,667,611,722,667,944,667,667,611,333,278,333,584,556,
278,556,611,556,611,556,333,611,611,278,278,556,278,889,611,611,
611,611,389,556,333,611,556,778,556,556,500,389,280,389,584,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,333,556,556,167,556,556,556,556,238,500,556,333,333,611,611,
0,556,556,556,278,0,556,350,278,500,500,556,1000,1000,0,611,
0,333,333,333,333,333,333,333,333,0,333,333,0,333,333,333,
1000,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,1000,0,370,0,0,0,0,611,778,1000,365,0,0,0,0,
0,889,0,0,0,278,0,0,278,611,944,611,0,0,834],
'helvetica-oblique': [
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
278,278,355,556,556,889,667,222,333,333,389,584,278,333,278,278,
556,556,556,556,556,556,556,556,556,556,278,278,584,584,584,556,
1015,667,667,722,722,667,611,778,722,278,500,667,556,833,722,778,
667,778,722,667,611,722,667,944,667,667,611,278,278,278,469,556,
222,556,556,500,556,556,278,556,556,222,222,500,222,833,556,556,
556,556,333,500,278,556,500,722,500,500,500,334,260,334,584,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,333,556,556,167,556,556,556,556,191,333,556,333,333,500,500,
0,556,556,556,278,0,537,350,222,333,333,556,1000,1000,0,611,
0,333,333,333,333,333,333,333,333,0,333,333,0,333,333,333,
1000,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,1000,0,370,0,0,0,0,556,778,1000,365,0,0,0,0,
0,889,0,0,0,278,0,0,222,611,944,611,0,0,834],
'symbol': [
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
250,333,713,500,549,833,778,439,333,333,500,549,250,549,250,278,
500,500,500,500,500,500,500,500,500,500,278,278,549,549,549,444,
549,722,667,722,612,611,763,603,722,333,631,722,686,889,722,722,
768,741,556,592,611,690,439,768,645,795,611,333,863,333,658,500,
500,631,549,549,494,439,521,411,603,329,603,549,549,576,521,549,
549,521,549,603,439,576,713,686,493,686,494,480,200,480,549,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,620,247,549,167,713,500,753,753,753,753,1042,987,603,987,603,
400,549,411,549,549,713,494,460,549,549,549,549,1000,603,1000,658,
823,686,795,987,768,768,823,768,768,713,713,713,713,713,713,713,
768,713,790,790,890,823,549,250,713,603,603,1042,987,603,987,603,
494,329,790,790,786,713,384,384,384,384,384,384,494,494,494,494,
0,329,274,686,686,686,384,384,384,384,384,384,494,494,790],
'times-bold': [
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
250,333,555,500,500,1000,833,333,333,333,500,570,250,333,250,278,
500,500,500,500,500,500,500,500,500,500,333,333,570,570,570,500,
930,722,667,722,722,667,611,778,778,389,500,778,667,944,722,778,
611,778,722,556,667,722,722,1000,722,722,667,333,278,333,581,500,
333,500,556,444,556,444,333,500,556,278,333,556,278,833,556,500,
556,556,444,389,333,556,500,722,500,500,444,394,220,394,520,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,333,500,500,167,500,500,500,500,278,500,500,333,333,556,556,
0,500,500,500,250,0,540,350,333,500,500,500,1000,1000,0,500,
0,333,333,333,333,333,333,333,333,0,333,333,0,333,333,333,
1000,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,1000,0,300,0,0,0,0,667,778,1000,330,0,0,0,0,
0,722,0,0,0,278,0,0,278,500,722,556,0,0,750],
'times-bolditalic': [
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
250,389,555,500,500,833,778,333,333,333,500,570,250,333,250,278,
500,500,500,500,500,500,500,500,500,500,333,333,570,570,570,500,
832,667,667,667,722,667,667,722,778,389,500,667,611,889,722,722,
611,722,667,556,611,722,667,889,667,611,611,333,278,333,570,500,
333,500,500,444,500,444,333,500,556,278,278,500,278,778,556,500,
500,500,389,389,278,556,444,667,500,444,389,348,220,348,570,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,389,500,500,167,500,500,500,500,278,500,500,333,333,556,556,
0,500,500,500,250,0,500,350,333,500,500,500,1000,1000,0,500,
0,333,333,333,333,333,333,333,333,0,333,333,0,333,333,333,
1000,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,944,0,266,0,0,0,0,611,722,944,300,0,0,0,0,
0,722,0,0,0,278,0,0,278,500,722,500,0,0,750],
'times-italic': [
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
250,333,420,500,500,833,778,333,333,333,500,675,250,333,250,278,
500,500,500,500,500,500,500,500,500,500,333,333,675,675,675,500,
920,611,611,667,722,611,611,722,722,333,444,667,556,833,667,722,
611,722,611,500,556,722,611,833,611,556,556,389,278,389,422,500,
333,500,500,444,500,444,278,500,500,278,278,444,278,722,500,500,
500,500,389,389,278,500,444,667,444,444,389,400,275,400,541,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,389,500,500,167,500,500,500,500,214,556,500,333,333,500,500,
0,500,500,500,250,0,523,350,333,556,556,500,889,1000,0,500,
0,333,333,333,333,333,333,333,333,0,333,333,0,333,333,333,
889,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,889,0,276,0,0,0,0,556,722,944,310,0,0,0,0,
0,667,0,0,0,278,0,0,278,500,667,500,0,0,750],
'times-roman': [
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
250,333,408,500,500,833,778,333,333,333,500,564,250,333,250,278,
500,500,500,500,500,500,500,500,500,500,278,278,564,564,564,444,
921,722,667,667,722,611,556,722,722,333,389,722,611,889,722,722,
556,722,667,556,611,722,722,944,722,722,611,333,278,333,469,500,
333,444,500,444,500,444,333,500,500,278,278,500,278,778,500,500,
500,500,333,389,278,500,500,722,500,500,444,480,200,480,541,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,333,500,500,167,500,500,500,500,180,444,500,333,333,556,556,
0,500,500,500,250,0,453,350,333,444,444,500,1000,1000,0,444,
0,333,333,333,333,333,333,333,333,0,333,333,0,333,333,333,
1000,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,889,0,276,0,0,0,0,611,722,889,310,0,0,0,0,
0,667,0,0,0,278,0,0,278,500,722,500,0,0,750],
'zapfdingbats': [
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
278,974,961,974,980,719,789,790,791,690,960,939,549,855,911,933,
911,945,974,755,846,762,761,571,677,763,760,759,754,494,552,537,
577,692,786,788,788,790,793,794,816,823,789,841,823,833,816,831,
923,744,723,749,790,792,695,776,768,792,759,707,708,682,701,826,
815,789,789,707,687,696,689,786,787,713,791,785,791,873,761,762,
762,759,759,892,892,788,784,438,138,277,415,392,392,668,668,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
0,732,544,544,910,667,760,760,776,595,694,626,788,788,788,788,
788,788,788,788,788,788,788,788,788,788,788,788,788,788,788,788,
788,788,788,788,788,788,788,788,788,788,788,788,788,788,788,788,
788,788,788,788,894,838,1016,458,748,924,748,918,927,928,928,834,
873,828,924,924,917,930,931,463,883,836,836,867,867,696,696,874,
0,874,760,946,771,865,771,888,967,888,831,873,927,970,234]
}

ascent_descent = {'Courier': (629, -157),
 'Courier-Bold': (626, -142),
 'Courier-BoldOblique': (626, -142),
 'Courier-Oblique': (629, -157),
 'Helvetica': (718, -207),
 'Helvetica-Bold': (718, -207),
 'Helvetica-BoldOblique': (718, -207),
 'Helvetica-Oblique': (718, -207),
 'Symbol': (0, 0),
 'Times-Bold': (676, -205),
 'Times-BoldItalic': (699, -205),
 'Times-Italic': (683, -205),
 'Times-Roman': (683, -217),
 'ZapfDingbats': (0, 0)}


def parseAFMfile(filename):
        """Returns an array holding the widths of all characters in the font.
        Ultra-crude parser"""
        alllines = open(filename, 'r').readlines()
        # get stuff between StartCharMetrics and EndCharMetrics
        metriclines = []
        between = 0
        for line in alllines:
                if 'endcharmetrics' in line.lower():
                    between = 0
                    break
                if between:
                    metriclines.append(line)
                if 'startcharmetrics' in line.lower():
                    between = 1
                        
        # break up - very shaky assumption about array size
        widths = [0] * 255
        
        for line in metriclines:
                chunks = line.split(';')
                
                (c, cid) = chunks[0].split()
                (wx, width) = chunks[1].split()
                #(n, name) = chunks[2].split()
                #(b, x1, y1, x2, y2) = chunks[3].split()
                widths[int(cid)] = int(width)
        
        # by default, any empties should get the width of a space
        for i in range(len(widths)):
                if widths[i] == 0:
                        widths[i] == widths[32]

        return widths


class FontCache:
        """Loads and caches font width information on demand.  Font names
        converted to lower case for indexing.  Public interface is stringwidth"""
        def __init__(self):
                global widths
                self.__widtharrays = widths

                
        def loadfont(self, fontname):
                filename = AFMDIR + os.sep + fontname + '.afm'
                print('cache loading',filename)
                assert os.path.exists(filename)
                widths = parseAFMfile(filename)
                self.__widtharrays[fontname] = widths
        def getfont(self, fontname):
                try:
                        return self.__widtharrays[fontname]
                except:
                        try:
                                self.loadfont(fontname)
                                return self.__widtharrays[fontname]
                        except:
                                # font not found, use Courier
                                print('Font',fontname,'not found - using Courier for widths')
                                return self.getfont('courier')
        

        def stringwidth(self, text, font):
                widths = self.getfont(font.lower())
                w = 0
                for char in text:
                        w = w + widths[ord(char)]
                return w
        def status(self):
                #returns loaded fonts
                return self.__widtharrays.keys()
                
TheFontCache = FontCache()

stringwidth = TheFontCache.stringwidth


##############################################################
#
#                       AI Document
#
##############################################################


class AIDocument:
        def __init__(self):
                self.objects = []
                self.info = AIHeader()  #hang onto it!
                self.add(self.info)
                self.transforms = AIStream()
                
                self.pages = []
                self.pagepositions = []
                self.infopos = 19
                
                # position 1
#               cat = AICatalog()
#               cat.RefPages = 3
#               cat.RefOutlines = 2
#               self.add(cat)
        
                # position 2 - outlines
#               outl = AIOutline()
#               self.add(outl)
        
                # position 3 - pages collection
#               self.PageCol = AIPageCollection()
#               self.add(self.PageCol)
        
                # positions 4-17 - fonts
#               fonts = MakeType1Fonts()
#               for font in fonts:
#                       self.add(font)
#       
#               self.fontdict = MakeFontDictionary(4, 15)
                
                # position 18 - Info


                                # testing here - position 19 - an image
                self.add(AIProlog())
                self.add(AISetUp())
#               self.add(AIStream())
#               self.add(AIImage())
                self.add(self.transforms)

        def add(self, obj):
                self.objects.append(obj)
                obj.doc = self

        def setTitle(self, title):
                "embeds in AI file"
                self.info.title = title
                
        def setAuthor(self, author):
                "embedded in AI file"
                self.info.author = author
                        
        def setBoundingBox(self, boundingbox):
                "embeds in AI file"
                self.transforms.originx = 0
                self.transforms.originy = 0
#               self.info.boundingBox = boundingbox
                lx,ly, ux,uy, tx = boundingbox
                print('setBoundingBox', lx,ly, ux,uy, tx)
                print('setBoundingBox', ux-lx,uy-ly)
                self.info.pagesize = (ux-lx), (uy-ly)
                ##XXX If the ArtSize is smaller than Letter Freehand always draws the 
                ##XXX origin as if the Art board was Letter sized, however the arboard 
                ##XXX is drawn at the same center as a letter sized artboard.
                ##XXX hence this translation 
                if ux-lx < 612:
                        self.transforms.originx = w = (612 - (ux-lx))/2 +tx
                        lx, ux = lx + w, ux + w
                if uy-ly < 792:
                        self.transforms.originy = w = (792 - (uy-ly))/2 +tx
                        ly, uy = ly + w, uy + w
#               print self.transforms
#               print self.transforms.originx
#               print self.transforms.originy
                print('setBoundingBox', lx,ly, ux,uy)
                self.info.boundingBox = lx, ly, ux, uy
                self.transforms.height = uy
                
        def setPage(self, page):
#               print 'setPage', page
                self.transforms.data = page
                
                        
        def SaveToFile(self, filename):
#               print 'SaveToFile', self.transforms.originx, self.transforms.originy
                f = open(filename, 'w')
                old_output = sys.stdout
                sys.stdout = f
                self.printAI()
                sys.stdout = old_output
                f.close()
        
        def printXref(self):
                self.startxref = sys.stdout.tell()
                print('xref')
                print(0,len(self.objects) + 1)
                print('0000000000 65535 f')
                for pos in self.xref:
                        print('%0.10d 00000 n' % pos)
        
        def printTrailer(self):
                print('''%%PageTrailer
gsave annotatepage grestore showpage
%%Trailer''')
#               print '<< /Size %d /Root %d 0 R /Info %d 0 R>>' % (len(self.objects) + 1, 1, self.infopos)
#               print 'startxref'
#               print self.startxref

        def printAI(self):
                "prints it to standard output.  Logs positions for doing trailer"
#               print "%AI-1.0"
#               print "%"
                i = 1
                self.xref = []
#               print self.objects
                for obj in self.objects:
#                       print 'printAI', obj
#                       pos = sys.stdout.tell()
#                       self.xref.append(pos)
#                       print i, '0 obj'
                        obj.printAI()
#                       print 'endobj'
#                       i = i + 1
#               self.printXref()
                self.printTrailer()
                print("%%EOF", end="")


        def addPage(self, page):
                """adds page and stream at end.  Maintains pages list"""
                #page.buildstream()
                pos = len(self.objects) # work out where added
                
#               page.ParentPos = 3   #pages collection
#               page.info = {'parentpos':3,
#                       'fontdict':self.fontdict,
#                       'contentspos':pos + 2}
                
#               self.PageCol.PageList.append(pos+1) 
#               print 'addPage', self.transforms.setStream((10, 20, 'm')) 
#               print 'addPage', self.transforms.setStream(page) 
#               self.page = 
                self.transforms.data = page
#               print 'addPage', self.page
#               self.objects.append(page)
#               self.objects.append(self.page)



##############################################################
#
#                       Utilities
#
##############################################################

class OutputGrabber:
        """At times we need to put something in the place of standard
        output.  This grabs stdout, keeps the data, and releases stdout
        when done.
        
        NOT working well enough!"""
        def __init__(self):
                self.oldoutput = sys.stdout
                sys.stdout = self
                self.closed = 0
                self.data = []
        def write(self, x):
                if not self.closed:
                        self.data.append(x)
        
        def getData(self):
                return "".join(self.data)

        def close(self):
                sys.stdout = self.oldoutput
                self.closed = 1
                
        def __del__(self):
                if not self.closed:
                        self.close()
        
                                
def testOutputGrabber():
        gr = OutputGrabber()
        for i in range(10):
                print('line',i)
        data = gr.getData()
        gr.close()
        print('Data...',data)
        

##############################################################
#
#                       AI Object Hierarchy
#
##############################################################



class AIObject:
        "Base class for all AI objects"
        def printAI(self):
                print('% base AI object')
        
                
class AILiteral(AIObject):
        " a ready-made one you wish to quote"
        def __init__(self, text):
                self.text = text
        def printAI(self):
                print(self.text)



class AICatalog(AIObject):
        "requires RefPages and RefOutlines set"
        def __init__(self):
                self.template = '''<<
/Type /Catalog
/Pages %d 0 R
/Outlines %d 0 R
>>'''
        def printAI(self):
                print(self.template % (self.RefPages, self.RefOutlines))

class AIHeader(AIObject):
        # no features implemented yet
        def __init__(self):
                self.title = "untitled"
                self.author = "anonymous"
                self.boundingBox = (0, 0, 565, 842)
                self.pagesize = (565, 842)
                self.rulerUnits = 2     
                now = time.localtime(time.time())
                self.datestr = time.strftime("%x %I:%M %p", now)
                                
        def printAI(self):
                print("%!PS-Adobe-3.0")
                print("%%Creator: PIDDLE Adobe Illustrator backend")
                print("%%Title: " +'(%s)' % self.title)
                print("%%For: " +'(%s)' % self.author)
                print("%%CreationDate: " +'(%s)' % self.datestr)
                print("%%DocumentProcessColors: Black""")
                print('%%BoundingBox: ' + '%s %s %s %s' % self.boundingBox)
                #%%DocumentProcessColors: Cyan Magenta Yellow
                #%%DocumentCustomColors: (PANTONE 156 CV)
                #%%RGBCustomColor: red green blue (customcolorname)
                #%%DocumentFonts: CooperBlack
                #%%+ Minion-Regular
                #%%DocumentFiles: WrathOfRalph
                print("%AI5_FileFormat 3")
                print("%AI3_ColorUsage: Color")
                print('%AI5_ArtSize: ' + '%s %s' % self.pagesize)
                print('%AI5_Templatebox: ' + '%s %s' % self.pagesize)
                #%AI7_ImageSettings: flag
                print('%AI5_TargetResolution: 300')
                print('%%EndComments')


class AIProlog(AIObject):
        "null outline, does nothing yet"
        def __init__(self):
                self.FontList = []
        def printAI(self):
                print('%%BeginProlog')
                print('%%EndProlog')

class AISetUp(AIObject):
        "null outline, does nothing yet"
        def __init__(self):
                self.FontList = []
        def printAI(self):
                print('%%BeginSetup')
                if self.FontList:
                        pass
                print('%%EndSetup')
        
class AIPageCollection(AIObject):
        "presumes PageList attribute set (list of integers)"
        def __init__(self):
                self.PageList = []
        def printAI(self):
                result = '<<\n/Type /Pages\n/Count %d\n/Kids [' % len(self.PageList)
                for page in self.PageList:
                        result = result + str(page) + ' 0 R '
                result = result + ']\n>>'
                print(result)

#class AIBody(AIObject):
#       """The Bastard.  Needs list of Resources etc. Use a standard one for now.
#       It manages a AIStream object which must be added to the document's list
#       os objects as well."""
#       def __init__(self):
#               self.drawables = []
#               self.stream = AIStream()
#               self.hasImages = 0
#               self.template = """<<
#/Type /Page
#/Parent %(parentpos)d 0 R
#/Resources 
#       << 
#       /Font %(fontdict)s
#       /ProcSet %(procsettext)s 
#       >>
#/MediaBox [0 0 595 842]
#/Contents %(contentspos)d 0 R
#>>"""
#       def printAI(self):
#               # check for image support
##              if self.hasImages:
##                      self.info['procsettext'] = '[/AI /Text /ImageC]'
##              else:
##                      self.info['procsettext'] = '[/AI /Text]'
##                      
##              print self.template % self.info
#               print "AIBody.printAI(self)"
#
#       def clear(self):
#               self.drawables = []
#       
#       def setStream(self, data):
#               self.stream.setStream(data)
#               
#
#       #def add(self, drawable):
#       #       self.drawables.append(drawable)
#       #
#       #def buildstream(self):
#       #       textmode = 0
#       #       
#       #       oldout = sys.stdout
#       #       fn = tempfile.mktemp()
#       #       #f = open(fn, 'wb')  #AR 19980202
#       #       f = open(fn, 'w')
#       #       sys.stdout = f
#       #       text = 0
#       #       for obj in self.drawables:
#       #               if obj.isText():
#       #                       if text == 0:
#       #                               print 'BT'
#       #                               text = 1
#       #               else:
#       #                       if text == 1:
#       #                               print 'ET'
#       #                               text = 0
#       #                               
#       #               obj.printAI()
#       #       if self.drawables[-1].isText():
#       #               print 'ET'
#       #       sys.stdout = oldout
#       #       f.close()
#       #               
#       #       self.stream = AIStream()
#       #       #self.stream.data = open(fn,'r').read()
#       #       self.stream.data = open(fn,'rb').read() #AR 19980202

TestStream = ['q', (72, 720, 'l'), 'S', 'Q', (80, 672, 'm'), (24, 'TL'),
(('Test Page with no stream'), 'Tj', 'T*')]


class AIStream(AIObject):
        "Used for the contents of a page"
        def __init__(self):
                self.data = []
                self.originx = 0
                self.originy = 0
                self.height = 0
        
#       def setStream(self, data):
#               self.data = data
#               print 'setStream', self.originy, self.originy
#               print self.data
                
        def printAI(self):
                # test code is useful
                if self.data == None:
                        self.data = TestStream
                # the AI length key should contain the length including
                # any extra LF pairs added by Print on DOS.
                
#               lines = len(string.split(self.data,'\n'))
#               length = len(self.data) + lines   # one extra LF each
                #length = len(self.data)        #AR 19980202
#               print 'printAI', self.originx, self.originy
#               print 'printAI', self.transformAI(self.originx, self.originy, self.height)

                        
#               print '<< /Length %d >>' % length
                print('''%AI5_BeginLayer
1 1 1 1 0 0 0 79 128 255 Lb
(Foreground) Ln''')
                print(self.transformAI(self.originx, self.originy, self.height))

#               print 'XXXX', self.data
                print('''LB
%AI5_EndLayer--''')

        def transformAI(self, ox, oy, ty):
#               print 'transformAI', ox, oy
#               print 'transformAI', self.data, type(self.data)
                page = []
                for line in self.data:
#                       print line
                        if isinstance(line, tuple) and  len(line) == 3:
                                page.append( "%f %f %f  rg" % line)
                        elif isinstance(line, tuple) and  len(line) == 7:
                                page.append( "%f %f %f %f %f %f %f  arc" % line )
                        else:
                                page.append( line )
                return "\n".join(page)
                        
class AIImage(AIObject):
                print("""<<
/Type /XObject
/Subtype /Image
/Name /Im0
/Width 24
/Height 23
/BitsPerComponent 1
/ColorSpace /DeviceGray
/Filter /ASCIIHexDecode
/Length 174
>>
stream
003B00 002700 002480 0E4940 114920 14B220 3CB650
75FE88 17FF8C 175F14 1C07E2 3803C4 703182 F8EDFC
B2BBC2 BB6F84 31BFC2 18EA3C 0E3E00 07FC00 03F800
1E1800 1FF800>
endstream
endobj""")
                        
class AIType1Font(AIObject):
        def __init__(self, key, font):
                self.fontname = font
                self.keyname = key
                self.template = """<<
/Type /Font
/Subtype /Type1
/Name /%s
/BaseFont /%s
/Encoding /WinAnsiEncoding
>>"""
        def printAI(self):
                print(self.template % (self.keyname, self.fontname))

class AIProcSet(AIObject):
        def printAI(self):
                print("[/AI /Text]")







##############################################################
#
#                       some helpers
#
##############################################################

def MakeType1Fonts():
        "returns a list of all the standard font objects"
        fonts = []
        pos = 1
        for fontname in StandardEnglishFonts:
                font = AIType1Font('F'+str(pos), fontname)
                fonts.append(font)
                pos = pos + 1
        return fonts

def MakeFontDictionary(startpos, count):
        "returns a font dictionary assuming they are all in the file from startpos"     
        dict = "                << \n"
        pos = startpos
        for i in range(count-1):
                dict = dict + '\t\t/F%d %d 0 R \n' % (i + 1, startpos + i)
        dict = dict + "         >>\n"
        return dict
        

#if __name__ == '__main__':
#       print 'For test scripts, run test1.py to test7.py'