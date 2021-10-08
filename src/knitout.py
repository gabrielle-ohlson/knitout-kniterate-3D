#!/usr/bin/env python3
# python3
# see example() for usage
import sys
import re
validHeaders = ['Carriers', 'Machine', 'Position', 'Yarn', 'Gauge']
############### helpers ######################################################


reg = re.compile("([a-zA-Z]+)([\+\-]?[0-9]+)")
def shiftCarrierSet(args, carriers):
    if len(args) == 0:
        raise AssertionError("No carriers specified")
    elif type(args[0] == list): #new (added in)
        args = args[0]
    for c in args:
        if not str(c) in carriers:
            raise ValueError("Carrier not specified in initial set", c)
    cs = ' '.join(str(c) for c in args)
    return cs

def shiftBedNeedle(args):
    if len(args) == 0:
        raise AssertionError("No needles specified")
    bn = args.pop(0)
    if  not (type(bn) == str or type(bn) == list or type(bn) == tuple):
        raise AssertionError("Invalid BedNeedle type")
    bed = None
    needle = None
    if type(bn) == str:
        m = reg.match(bn)
        if not m and (bn == 'f' or bn == 'b' or bn == 'fs' or bn == 'bs'):
            bed = bn
            if not len(args):
                raise ValueError("Needle not specified")
            if  isinstance(args[0],int) or args[0].isdgit():
                needle = int(args.pop(0))

        else:
            if (m.group(1) == 'f' or m.group(1) == 'b' or m.group(1) == 'fs' or m.group(1) == 'bs'):
                bed = m.group(1)
            else:
                raise ValueError("Invalid bed type. Must be 'f' 'b' 'fs' 'bs'.")
            if m.group(2):
                needle = m.group(2)
            else:
                raise ValueError("Invalid needle. Must be numeric.", m.group(2))
    else:
        if len(bn) != 2:
            raise ValueError("Bed and Needle need to be supplied.")
        if (bn[0] == 'f' or bn[0] == 'b' or bn[0] == 'fs' or bn[0] == 'bs'):
            bed = bn[0]
        else:
            raise ValueError("Invalid bed type. Must be 'f' 'b' 'fs' 'bs'.")
        if type(bn[1]) == int or bn[1].isdigit():
            needle = int(bn[1])
        else:
            raise ValueError("2.Invalid needle. Must be numeric.")

    return bed + str(needle)

def shiftDirection(args):
    if len(args) == 0:
        raise AssertionError("No direction specified")
    direction = args.pop(0)
    if direction != '+' and direction != '-':
        raise ValueError("Invalid direction: " + direction)
    return direction

##############################################################################


class Writer:

    def __init__(self, cs):
        # array of carrier names, front-to-back
        self.carriers = list()
        # array of operations, strings
        self.operations = list()
        # array of headers, strings
        self.headers = list()

        self.carriers = cs.split()
        self.addHeader('Carriers', cs);
    def addHeader(self, name, value):
        if not name in validHeaders:
            raise ValueError("Unknown header, must be " + ' '.join(validHeaders) + "; " + name)
        self.headers.append(';;' + name + ': ' + value)

    def addRawOperation(self, op):
        self.operations.append(op)

    def ingripper(self, *args):
        argl = list(args)
        self.operations.append('in ' +  shiftCarrierSet(argl, self.carriers))


    def inhook(self, *args):
        argl = list(args)
        self.operations.append('inhook ' + shiftCarrierSet(argl, self.carriers))

    def incarrier(self, *args):
        argl = list(args)
        self.operations.append('in ' + shiftCarrierSet(argl, self.carriers))

    def outgripper(self, *args):
        argl = list(args)
        self.operations.append('out ' + shiftCarrierSet(argl, self.carriers))


    def outhook(self, *args):
        argl = list(args)
        self.operations.append('outhook ' + shiftCarrierSet(argl, self.carriers))

    def outcarrier(self, *args):
        argl = list(args)
        self.operations.append('out ' + shiftCarrierSet(argl, self.carriers))

    def releasehook(self, *args):
        argl = list(args)
        self.operations.append('releasehook ' + shiftCarrierSet(argl, self.carriers))


    def rack(self, r):
        if not (type(r) == int or type(r) == float or (type(r) == str and r.isdigit())):
            raise ValueError("Rack is not an integer or fraction")
        #TODO only certain values make sense
        self.operations.append('rack ' + str(r))


    def knit(self, *args):
        argl = list(args)
        direction = shiftDirection(argl)
        bn = shiftBedNeedle(argl)
        cs = shiftCarrierSet(argl, self.carriers)
        self.operations.append('knit ' + direction + ' ' + bn + ' ' + cs)

    def tuck(self, *args):
        argl = list(args)
        direction = shiftDirection(argl)
        bn = shiftBedNeedle(argl)
        cs = shiftCarrierSet(argl, self.carriers)
        self.operations.append('tuck ' + direction + ' ' + bn + ' ' + cs)


    def xfer(self, *args):
        argl = list(args)
        bn_from = shiftBedNeedle(argl)
        bn_to = shiftBedNeedle(argl)
        self.operations.append('xfer ' + bn_from + ' ' + bn_to)


    def split(self, *args):
        argl = list(args)
        direction  = shiftDirection(argl)
        bn_from = shiftBedNeedle(argl)
        bn_to = shiftBedNeedle(argl)
        cs = shiftCarrierSet(argl, self.carriers)
        self.operations.append('split '+ direction + ' '  + bn_from + ' ' + bn_to + ' ' + cs)


    def miss(self, *args):
        argl = list(args)
        direction = shiftDirection(argl)
        bn = shiftBedNeedle(argl)
        cs = shiftCarrierSet(argl, self.carriers)
        self.operations.append('miss ' + direction + ' ' + bn + ' ' + cs)

    def drop(self, *args):
        argl = list(args)
        bn = shiftBedNeedle(argl)
        self.operations.append('drop ' + bn)

    def amiss(self, *args):
        argl = list(args)
        bn = shiftBedNeedle(argl)
        self.operations.append('amiss ' + bn)

    def pause(self, message=''):
        self.operations.append(f'pause {message}')

    def comment(self, commentString):
        if type(commentString) != str:
            raise ValueError('comment has to be string')
        self.operations.append(';' + commentString)

    def kcodecomment(self, commentString):
        if type(commentString) != str:
            raise ValueError('comment has to be string')
        self.operations.append(';kniterate ' + commentString)

    #Extensions

    def stitchNumber(self, val):
        self.operations.append('x-stitch-number ' + str(val))

    def xferStitchNumber(self, val):
        self.operations.append('x-xfer-stitch-number ' + str(val))

    def speedNumber(self, val):
        self.operations.append('x-speed-number ' + str(val))

    def rollerAdvance(self, val):
        self.operations.append('x-roller-advance ' + str(val))

    def addRollerAdvance(self,val):
        self.operations.append('x-add-roller-advance ' + str(val))

    def stoppingDistance(self,val):
        self.operations.append('x-carrier-stopping-distance ' + str(val))

    def fabricPresser(self, mode):
        if not (mode == 'auto' or mode == 'on' or mode == 'off'):
            raise ValueError("Mode must be one of 'auto','on','off' : "+ str(mode))
        self.operations.append('x-presser-mode ' + mode)

    #--- FUNCTIONS ADDED BY GABRIELLE ---
    #function for going back to make a twisted stitch
    def twist(self, bedNeedle_s, rollerAdvanceOffset=None): #bedNeedle_s can be just a single bed-needle, or a list to go through multiple
        if type(bedNeedle_s) == str: bedNeedle_s = [bedNeedle_s]

        if rollerAdvanceOffset is not None: rollerAdvanceOffset = f'x-add-roller-advance {rollerAdvanceOffset}'
        
        leftovers = [] #bed needles that we're found

        for bn in bedNeedle_s:
            for o in range (len(self.operations)-1, 0, -1):
                if f'xfer {bn}' in self.operations[o]: #new #check #v
                    leftovers.append(bn) 
                    break #^
                if 'knit' in self.operations[o] and bn in self.operations[o]:
                    line = self.operations[o]
                    originalDir = line.split()[1]
                    if originalDir == '-': twistDir = '+'
                    else: twistDir = '-'
                    missLine = line.replace('knit', 'miss')
                    twistLine = line.replace(originalDir, twistDir)
                    if rollerAdvanceOffset is not None: self.operations[o:o+1] = ';twisted stitch', rollerAdvanceOffset, missLine, rollerAdvanceOffset, twistLine
                    else: self.operations[o:o+1] = ';twisted stitch', missLine, twistLine
                    break
        
        return leftovers


    #function for going back to make a split stitch
    def switchToSplit(self, *args):
        argl = list(args)
        direction  = shiftDirection(argl)
        bn_from = shiftBedNeedle(argl)
        bn_to = shiftBedNeedle(argl)
        cs = shiftCarrierSet(argl, self.carriers)

        for o in range (len(self.operations)-1, 0, -1):
            if 'knit' in self.operations[o] and bn_from in self.operations[o]:
                self.operations[o] = f'split {direction} {bn_from} {bn_to} {cs}'
                break
    

    def tuckOverSplit(self, tuckCarrier, tuckDirection, *args):
        '''
        *args: if no argument is passed, will just tuck over most recent split. if one argument, assumes that argument is the number of splits that should be skipped over to find the split that is meant to be tucked over. if two arguments, assumes the argument 1 == bn_from and argument 2 == bn_to
        '''
        # direction = None
        bn_from = None
        bn_to = None
        otherDir = None

        offLimits = []
        if len(args) <= 1:
            if len(args) == 0: splitSkipCount = 0
            else: splitSkipCount = args[0]
            splitCount = -1
            for op in reversed(self.operations):
                info = op.split()
                if info[0] == 'tuck':
                    offLimits.append(info[2])
                if info[0] == 'split':
                    splitCount += 1
                    if splitCount == splitSkipCount:
                        # direction = info[1]
                        otherDir = info[1]
                        bn_from = info[2]
                        bn_to = info[3]

                        
                        break
                    else: continue
            # info = self.operations[len(self.operations)-1]
            # if 'split ' in info:
            #     info = info.split()
            #     direction = info[1]
            #     bn_from = info[2]
            #     bn_to = info[3]
            #     # bed = bn_to[0]
            #     # needle = int(bn_to[1:])
            if bn_from is None: raise ValueError(f"Couldn't find a split.")
        else: 
            info = list(args)
            # direction = info[0]
            # bn_from = info[1]
            # bn_to = info[2]
            bn_from = info[0]
            bn_to = info[1]

        bed_from = bn_from[0]
        needle_from = int(bn_from[1:])
        bed_to = bn_to[0]
        needle_to = int(bn_to[1:])

        if otherDir is None:
            if tuckDirection == '+': otherDir = '-'
            else: otherDir = '+'

        if otherDir == '-': outNeedle = needle_to-2
        else: outNeedle = needle_to+2

        # if tuckDirection == '+':
        #     otherDir = '-'
        #     outNeedle = needle_to-2
        # else:
        #     otherDir = '+'
        #     outNeedle = needle_to+2

        
        for op in reversed(self.operations):
            if op.split()[0] == 'rack':
                currentRack = int(op.split()[1])
                if bed_from == 'b' and needle_from+currentRack == needle_to:
                    if currentRack == 0 and tuckDirection == '+': self.operations.append('rack -0.25') #check
                    else: self.operations.append('rack 0.25')
                elif bed_from == 'f' and needle_to+currentRack == needle_from:
                    if currentRack == 0 and tuckDirection == '-': self.operations.append('rack -0.25')
                    else: self.operations.append('rack 0.25')
                else: currentRack is None
                # if (bed_from == 'b' and needle_from+rack == needle_to) or (bed_from == 'f' and needle_to+rack == needle_from):
                #     if currentRack == 0: self.operations.append('rack 0.25')
                #     else: self.operations.append()
                # else: currentRack is None
                break

        if f'{bed_from}{needle_to}' not in offLimits: self.operations.append(f'tuck {tuckDirection} {bed_from}{needle_to} {tuckCarrier}')
        else:
            if tuckDirection == '+': add = 2
            else: add = -2
            newTuckFound = False
            newTuck = needle_to+add
            while not newTuckFound:
                if f'{bed_from}{newTuck}' not in offLimits:
                    self.operations.append(f'tuck {tuckDirection} {bed_from}{newTuck} {tuckCarrier}')
                    newTuckFound = True
                    break
                else: newTuck += add

        if f'{bed_to}{needle_from}' not in offLimits: self.operations.append(f'tuck {tuckDirection} {bed_to}{needle_from} {tuckCarrier}')
        else:
            if tuckDirection == '+': add = 2
            else: add = -2
            newTuckFound = False
            newTuck = needle_from+add
            while not newTuckFound:
                if f'{bed_to}{newTuck}' not in offLimits:
                    self.operations.append(f'tuck {tuckDirection} {bed_to}{newTuck} {tuckCarrier}')
                    newTuckFound = True
                    break
                else: newTuck += add

        self.operations.append(f'tuck {otherDir} {bed_from}{outNeedle} {tuckCarrier}')
        if currentRack is not None: self.operations.append(f'rack {currentRack}')

        return [f'{bed_from}{outNeedle}', f'{bed_from}{needle_to}', f'{bed_to}{needle_from}'] #to drop

    def deleteLastOp(self, kwd_s=None, breakCondition=None, returnOp=False):
    # def deleteLastOp(self, kwd=None, searchRange=None, breakCondition=None):
        if kwd_s is None:
            lastOp = self.operations.pop()
            if returnOp: return lastOp
            else: return True
        else:
            # if searchRange is None: stop = 0
            # else:
            #     stop = len(self.operations)-2-searchRange
            #     if stop < 0: stop = 0
            
            found = False
            # for o in range(len(self.operations)-1, stop, -1):
            for o in range(len(self.operations)-1, 0, -1):
                if breakCondition is not None and breakCondition(self.operations[o]): break

                if type(kwd_s) == list:
                    if all(str(word) in self.operations[o] for word in kwd_s): found = True
                elif kwd_s in self.operations[o]: found = True

                if found:
                    lastOp = self.operations[o]
                    del self.operations[o]
                    if returnOp: return lastOp
                    else: return True
                    break
                # if kwd in self.operations[o]:
                #     del self.operations[o]
                #     found = True
                #     break
            return found #will be False
            # if not found: print(f"WARNING: Couldn't find operation matching keyword: {kwd}, so didn't delete anything.") #remove #?


    def returnLastOp(self, op=None, direction=None, bn1=None, bn2=None, carrier=None, asDict=False, *otherKwds): #TODO: check that option for multiple carriers works
        args = filter(lambda el: el is not None and el is not self and type(el) != bool and len(el), list(locals().values()))
        args = list(args)
        # otherKwds = list(otherKwds)
        # split + f10
        # xfer f10
        if bn1 is not None:
            b1 = bn1[:1]
            n1 = int(bn1[1:])
        else:
            b1 = None
            n1 = None
        if bn2 is not None:
            b2 = bn2[:1]
            n2 = int(bn2[1:])
        else:
            b2 = None
            n2 = None
        
        opList = []
        if type(op) == list: #multiple ops allowd
            opList = op.copy()
            op = None

        lastOp = {'op': op, 'direction': direction, 'bn1': {'bed': b1, 'needle': n1}, 'bn2': {'bed': b2, 'needle': n2}, 'carrier': carrier, 'rack': None}

        for line in reversed(self.operations):
            if not all(x in line for x in args): continue

            info = line.split()
            
            if info[0][0] == ';' and ((op is not None and op != 'comment' and op != ';') or direction is not None or bn1 is not None or bn2 is not None or carrier is not None): continue #move on if the whole line is a comment and we aren't looking for a comment
            info = [x for x in info if(x[0] != ';')] # remove comments

            # if not [el for el in args if(el in line)]: 
            # if op is not None and info[0] != op:
            if (op is not None and info[0] != op) or (len(opList) and info[0] not in opList):
                continue
            else: lastOp['op'] = info[0]
            if direction is not None and info[1] != direction:
                continue
            else: lastOp['direction'] = info[1]
            if bn2 is not None and (info[0] != 'xfer' or info[0] != 'split'): continue
            
            elif bn1 is not None and (len(info) < 3 or (info[0] == 'xfer' and info[1] != bn1) or info[2] != bn1): continue #bn1 or bn2 #? #*
            elif carrier is not None and ((type(carrier) == list and info[len(info)-1] not in carrier and info[len(info)-2] not in carrier) or (type(carrier) == str and info[-1] != carrier) or 'x-' in info[0] or 'rack' in info[0]): continue
            # elif carrier is not None and info[len(info)-1] != carrier or 'x-' in info[0] or 'rack' in info[0]: continue
            else:
                if asDict:
                    lastOp['op'] = info[0]
                    if len(info) == 1: return lastOp

                    if info[0] == 'rack': lastOp['rack'] = info[1]
                    elif info[0] == 'drop': lastOp['bn1'] = {'bed': info[1][:1], 'needle': int(info[1][1:])}
                    elif info[0] == 'in' or info[0] == 'out':
                        if len(info) > 2 and ';' not in info[2]: lastOp['carrier'] = [info[1], info[2]]
                        else: lastOp['carrier'] = info[1]
                    elif info[1] == '+' or info[1] == '-':
                        lastOp['direction'] = info[1]
                        lastOp['bn1'] = {'bed': info[2][:1], 'needle': int(info[2][1:])}
                        if 'f' in info[3] or 'b' in info[3]: #split
                            lastOp['bn2'] = {'bed': info[3][:1], 'needle': int(info[3][1:])}
                            if len(info) > 5 and ';' not in info[5]: lastOp['carrier'] = [info[4], info[5]]
                            else: lastOp['carrier'] = info[4]
                            # lastOp['carrier'] = info[4]
                        else:
                            if len(info) > 4 and ';' not in info[4]: lastOp['carrier'] = [info[3], info[4]]
                            else: lastOp['carrier'] = info[3]
                            # lastOp['carrier'] = info[3]
                    elif info[0] == 'xfer':
                        lastOp['bn1'] = {'bed': info[1][:1], 'needle': int(info[1][1:])}
                        lastOp['bn2'] = {'bed': info[2][:1], 'needle': int(info[2][1:])}
                    return lastOp
                else: return line

        return None #return None is nothing is found  


    def clear(self):
        #clear buffers
        self.headers = list()
        self.operations = list()

    def write(self, filename):
        print(f'Writing {filename} ...')
        version = ';!knitout-2\n'
        content = version + '\n'.join(self.headers) + '\n' +  '\n'.join(self.operations)
        try:
            # with open(filename, "w") as out:
            #     print(content, file=out)
            #     print('wrote file ' + filename)
            # # with open(filename, "w") as out:
            # #     sys.stdout = out
            # #     print(content)
            ''' ----- '''
            out = open(filename,'w')
            sys.stdout = out
            print(content)
            out.close()
        except IOError as error:
            print('Could not write to file ' + filename)
        

def example():
    stockinette_rectangle()
    garter_rectangle()
    rib_rectangle()
    cable_rectangle()
    stockinette_band()

def stockinette_rectangle(width=10, height=20):
    writer = Writer('1 2 3 4')
    writer.addHeader('Machine', 'swg')
    carrier = '1'
    writer.inhook(carrier)
    for i in range(width-1, 0, -2):
        writer.tuck('-', ('f',i), carrier)
    writer.releasehook(carrier)
    for i in range(0, width, 2):
        writer.tuck('+', ('f', i), carrier)
    for j in range(0, height):
        if j%2 == 0:
            for i in range(width, 0,-1):
                writer.knit('-', ('f', i-1), carrier)
        else:
            for i in range(0, width):
                writer.knit('+', ('f', i), carrier)

    writer.outhook(carrier)
    for i in range(0, width):
        writer.drop(('f', i))

    writer.write('stockinette-'+str(width)+'x'+str(height)+'.k')

def garter_rectangle(width=10, height=20):
    writer = Writer('1 2 3 4')
    writer.addHeader('Machine', 'swg')
    carrier = '1'
    writer.inhook(carrier)
    for i in range(width-1, 0, -2):
        writer.tuck('-', ('f',i), carrier)
    writer.releasehook(carrier)
    for i in range(0, width, 2):
        writer.tuck('+', ('f', i), carrier)
    for j in range(0, height):
        if j%2 == 0:
            for i in range(width, 0,-1):
                writer.knit('-', ('f', i-1), carrier)
        else:
            for i in range(0, width):
                writer.xfer(('f',i), ('b',i))
            for i in range(0, width):
                writer.knit('+', ('b', i), carrier)
            for i in range(0, width):
                writer.xfer(('b',i), ('f',i))

    writer.outhook(carrier)
    for i in range(0, width):
        writer.drop(('f', i))

    writer.write('garter-'+str(width)+'x'+str(height)+'.k')

def rib_rectangle(width=10, height=20):
    writer = Writer('1 2 3 4')
    writer.addHeader('Machine', 'swg')
    carrier = '1'
    writer.inhook(carrier)
    for i in range(width-1, 0, -2):
        bed = 'f'
        if i%2:
            bed = 'b'
        writer.tuck('-', (bed,i), carrier)

    writer.releasehook(carrier)

    for i in range(0, width, 2):
        bed = 'f'
        if i%2:
            bed = 'b'

        writer.tuck('+', (bed, i), carrier)
    for j in range(0, height):
        if j%2 == 0:
            for i in range(width, 0,-1):
                bed = 'f'
                if (i-1)%2:
                    bed = 'b'
                writer.knit('-', (bed, i-1), carrier)
        else:
            for i in range(0, width):
                bed = 'f'
                if i%2:
                    bed = 'b'
                writer.knit('+', (bed, i), carrier)

    writer.outhook(carrier)
    for i in range(0, width):
        writer.drop(('f', i))
        writer.drop(('b', i))

    writer.write('rib-'+str(width)+'x'+str(height)+'.k')

#to test xfers, rack:
def cable_rectangle(width=30, height=40):
    writer = Writer('1 2 3 4')
    writer.addHeader('Machine', 'swg')
    carrier = '1'
    mid = int(width/2)
    writer.inhook(carrier)
    for i in range(width-1, 0, -2):
        writer.tuck('-', ('f',i), carrier)

    writer.releasehook(carrier)
    for i in range(0, width, 2):
        writer.tuck('+', ('f', i), carrier)
    for j in range(0, height):
        if j%2 == 0:
            for i in range(width, 0,-1):
                writer.knit('-', ('f', i-1), carrier)
        else:
            for i in range(0, width):
                writer.knit('+', ('f', i), carrier)
        if j > 2 and j < height-2 and j%4==0: #every 4th row
            writer.comment("cable op at row " + str(j))
            writer.xfer('f', mid-2, 'b', mid-2)
            writer.xfer('f', mid-1, 'b', mid-1)
            writer.xfer('f', mid, 'b', mid)
            writer.xfer('f', mid+1, 'b', mid+1)
            writer.rack(2)
            writer.xfer('b',mid-2, 'f', mid)
            writer.xfer('b',mid-1, 'f', mid+1)
            writer.rack(-2)
            writer.xfer('b',mid, 'f', mid-2)
            writer.xfer('b',mid+1, 'f', mid-1)
            writer.rack(0)
    writer.outhook(carrier)
    for i in range(0, width):
        writer.drop(('f', i))

    writer.write('cable-'+str(width)+'x'+str(height)+'.k')

#to test split
def stockinette_band(width=20, height=40):
    writer = Writer('1 2 3 4')
    writer.addHeader('Machine', 'swg')
    carrier = '1'
    writer.inhook(carrier)
    for i in range(width-1, 0, -2):
        writer.tuck('-', ('f',i), carrier)

    writer.releasehook(carrier)
    for i in range(0, width, 2):
        writer.tuck('+', ('f', i), carrier)

    for j in range(0, height):
        if j%2 == 0:
            for i in range(width, 0,-1):
                writer.knit('-', ('f', i-1), carrier)
        else:
            if j == 1:
                for i in range(0, width):
                    writer.split('+','f',i,'b',i, carrier)
            else:
                for i in range(0, width):
                    writer.knit('+', ('f', i), carrier)


    for i in range(0, width):
        writer.xfer('b',i,'f',i)

    if height%2 == 0:
        for i in range(width, 0,-1):
            writer.knit('-', ('f', i-1), carrier)
        for i in range(0, width):
            writer.knit('+', ('f', i), carrier)


    else:
        for i in range(0, width):
            writer.knit('+', ('f', i), carrier)
        for i in range(width, 0,-1):
            writer.knit('-', ('f', i-1), carrier)

    #todo bindoff
    writer.outhook(carrier)
    for i in range(0, width):
        writer.drop(('f', i))

    writer.write('band-'+str(width)+'x'+str(height)+'.k')

#todo tubes, castons, bindoffs