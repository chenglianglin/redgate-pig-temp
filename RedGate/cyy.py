#!/usr/bin/python

# USE_PIG = True
USE_PIG = False
# from __future__ import with_statement
if USE_PIG:
    from org.apache.pig.scripting import Pig

import json


from codeGenTable import codeGenTable
# from pprint import pprint


# class Binder:
#   @staticmethod
#   def bindParams(script,params)
#   """
#   script : pig code string
#   params : params dictionary
#   """
#     for key,value in params.iteritems:
#         script.replace('$'+key,value)
#     return script


def bindParams(script, paramsDic):
    for key, value in paramsDic.iteritems():
        script = script.replace('$' + key, value)

    return script


def getModuleFieldsList(moduleName):
    script = codeGenTable[moduleName]
    # getting the loading statement from whole code
    script = script.split('\n')[1]
    n = script.rfind('(')
    m = script.rfind(')')
    fieldsString = script[n + 1:m].strip()
    fieldsString = ''.join(fieldsString.split())
    fieldsList = fieldsString.split(',')
    for i in range(0, len(fieldsList)):
        fieldsList[i] = moduleName + "::" + fieldsList[i]
    return fieldsList


def genStringFromList(l):
    outString = ""
    for i in l:
        outString += str(i) + ", "

    return outString[:len(outString) - 2]


def genSchemaStringByList(schemaList):
    n = len(schemaList)
    joinKeyFlag = False
    genFields = []
    genSchema = []
    for i in range(0, n):
        appendString = schemaList[i]

        # TODO:need fix
        if appendString == "UserId":
            appendField = appendString
        else:
            print appendString
            appendField = appendString.split("::")[1]
            appendField = appendField.split(":")[0]

        # TODO: should change join key (UserId here) to variable
        if (appendField == "UserId"):
            if joinKeyFlag is False:
                genFields.append("$" + str(i))
                genSchema.append(appendField)
                joinKeyFlag = True

        else:
            genFields.append("$" + str(i))
            genSchema.append(appendString)

        assert len(genFields) == len(genSchema), " ERROR in genSchemaStringByList: genFields should equals to genSchema "

        print len(schemaList)

    # TODO pass out newSchemaList is an ugly way
    return {'genFields': genStringFromList(genFields),
            'genSchema': genStringFromList(genSchema), 'newSchemaList': genSchema}

if __name__ == "__main__":

    print "======================start==================="
    print "======================start==================="
    print "======================start==================="
    print "======================start==================="

    print getModuleFieldsList('A1')
    print getModuleFieldsList('B')
    print getModuleFieldsList('C')
    print getModuleFieldsList('D')
    print "======================debugging==================="

    with open('paramsOri.json') as data_file:
        jsonArr = json.load(data_file)

    # pprint(params)
    # params=[["A1",5],["B",5],["C",5]]

    pigString = "REGISTER /usr/lib/hbase/lib/*.jar;"

    # run all module individually
    for i in jsonArr:
        script = codeGenTable[i['action']]
        script = bindParams(script, i['params'])
        pigString += script

    postString = ""
    curSchemaList = []
    # combine modules
    for i in range(0, len(jsonArr)):
        currentAction = jsonArr[i]['action']
        curSchemaList += getModuleFieldsList(currentAction)
        print "CYYD2 :" + str(i) + ": " + str(curSchemaList)
        if i == 0:
            postString = "Result = " + currentAction + "Result;\n"
            # postString += "DESCRIBE Result;\n"

        else:

            postString += "Result = JOIN Result BY UserId, " + currentAction + "Result BY UserId;\n"
            # TODO:curSchemaList is modified in the function
            print len(curSchemaList)
            print curSchemaList
            fsDic = genSchemaStringByList(curSchemaList)
            curSchemaList = fsDic['newSchemaList']
            print curSchemaList
            # print("=======generated SchemaString: "+genSchemaStringByList(curSchemaList)+"\n")
            postString += "Result = FOREACH Result GENERATE " + fsDic['genFields'] + ";\n"
            postString += "Result = FOREACH Result GENERATE * AS (" + fsDic['genSchema'] + ");\n"

            # postString += "Result = FOREACH Result GENERATE " + currentAction+ "Result::UserId AS UserId, *;\n"
            # postString += "DESCRIBE Result;\n"

    # A1BResult = JOIN BResult BY UserId, CResult By UserId;
    pigString += postString
    pigString += """
    DUMP Result;
    DESCRIBE Result;
    """

    print(pigString)

    # with open('cyygeneratedPig.pig','w') as outFile:
    #    outFile.write(pigString)
    if USE_PIG:
        P = Pig.compile(pigString)
        # P = Pig.compileFromFile('pig_bcd_bc.pig')

    # run the pig script

        if True:
            result = P.bind().runSingle()

            if result.isSuccessful():
                print 'run success'
            else:
                raise 'run failed'
