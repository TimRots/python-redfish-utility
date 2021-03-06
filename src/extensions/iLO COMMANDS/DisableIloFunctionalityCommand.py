###
# Copyright 2019 Hewlett Packard Enterprise, Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

# -*- coding: utf-8 -*-
""" iLO Functionality Command for rdmc """
import sys
import json

from argparse import ArgumentParser

from rdmc_base_classes import RdmcCommandBase, add_login_arguments_group
from rdmc_helper import ReturnCodes, InvalidCommandLineError, InvalidCommandLineErrorOPTS, \
                    NoContentsFoundForOperationError, IncompatableServerTypeError, Encryption

class DisableIloFunctionalityCommand(RdmcCommandBase):
    """ Disables iLO functionality to the server """
    def __init__(self, rdmcObj):
        RdmcCommandBase.__init__(self,\
            name='disableilofunctionality',\
            usage='disableilofunctionality [OPTIONS]\n\n\t'\
                'Disable iLO functionality on the current logged in server.' \
                '\n\texample: disableilofunctionality\n\n\tWARNING: this will' \
                ' render iLO unable to respond to network operations.\n\n\t'\
                'Add the --force flag to ignore critical task checking.',\
            summary="disables iLO's accessibility via the network and resets "\
            "iLO. WARNING: This should be used with caution as it will "\
            "render iLO unable to respond to further network operations "\
            "(including REST operations) until iLO is re-enabled using the"\
            " RBSU menu.",\
            aliases=None,\
            argparser=ArgumentParser())
        self.definearguments(self.parser)
        self._rdmc = rdmcObj
        self.typepath = rdmcObj.app.typepath
        self.lobobj = rdmcObj.commands_dict["LoginCommand"](rdmcObj)
        self.selobj = rdmcObj.commands_dict["SelectCommand"](rdmcObj)
        self.getobj = rdmcObj.commands_dict["GetCommand"](rdmcObj)

    def run(self, line):
        """ Main DisableIloFunctionalityCommand function

        :param line: string of arguments passed in
        :type line: str.
        """

        try:
            (options, args) = self._parse_arglist(line)
        except (InvalidCommandLineErrorOPTS, SystemExit):
            if ("-h" in line) or ("--help" in line):
                return ReturnCodes.SUCCESS
            else:
                raise InvalidCommandLineErrorOPTS("")

        if args:
            raise InvalidCommandLineError("disableilofunctionality command takes no arguments.")

        self.ilofunctionalityvalidation(options)

        select = 'Manager.'
        results = self._rdmc.app.select(selector=select)

        try:
            results = results[0]
        except:
            pass

        if results:
            path = results.resp.request.path
        else:
            raise NoContentsFoundForOperationError("Manager. not found.")

        bodydict = results.resp.dict['Oem'][self.typepath.defs.oemhp]
        if bodydict['iLOFunctionalityRequired']:
            raise IncompatableServerTypeError("disableilofunctionality"\
                " command is not available. iLO functionality is required"\
                " and can not be disabled on this platform.")

        try:
            for item in bodydict['Actions']:
                if 'iLOFunctionality' in item:
                    if self.typepath.defs.isgen10:
                        action = item.split('#')[-1]
                    else:
                        action = "iLOFunctionality"

                    path = bodydict['Actions'][item]['target']
                    body = {"Action": action}
                    break
        except:
            body = {"Action": "iLOFunctionality", \
                                "Target": "/Oem/Hp"}

        if self.ilodisablechecks(options):

            sys.stdout.write("Disabling iLO functionality. iLO will be "\
                             "unavailable on the logged in server until it is "\
                             "re-enabled manually.\n")

            results = self._rdmc.app.post_handler(path, body, silent=True, \
                                    service=True, response=True)

            if results.status == 200:
                sys.stdout.write("[%d] The operation completed successfully.\n" % results.status)
            else:
                sys.stdout.write("[%d] iLO responded with the following info: \n" % results.status)
                json_payload = json.loads(results._http_response.data)
                try:
                    sys.stdout.write("%s" % json_payload['error']\
                                     ['@Message.ExtendedInfo'][0]['MessageId'])
                except:
                    sys.stdout.write("An invalid or incomplete response was"\
                                     " received: %s\n" % json_payload)

        else:
            sys.stdout.write("iLO is currently performing a critical task and "\
                             "can not be safely disabled at this time. Please try again later.\n")

        return ReturnCodes.SUCCESS

    def ilodisablechecks(self, options):
        """ Verify it is safe to actually disable iLO

        :param options: command line options
        :type options: values, attributes of class obj
        """

        if options.force:
            sys.stdout.write('Force Enabled: Ignoring critical operation/mode checking.\n')
            return True

        else:
            keyword_list = 'idle', 'complete'

            try:
                results = self._rdmc.app.select(selector='UpdateService.')[0]
            except:
                raise NoContentsFoundForOperationError("UpdateService. not found.")

            try:
                state = results.resp.dict['Oem']['Hpe']['State'].lower()
                for val in keyword_list:
                    if val in state:
                        return True
                return False

            except:
                raise NoContentsFoundForOperationError("iLO state not identified")

    def ilofunctionalityvalidation(self, options):
        """ ilofunctionalityvalidation method validation function

        :param options: command line options
        :type options: list.
        """
        client = None
        inputline = list()

        try:
            client = self._rdmc.app.current_client
        except:
            if options.user or options.password or options.url:
                if options.url:
                    inputline.extend([options.url])
                if options.user:
                    if options.encode:
                        options.user = Encryption.decode_credentials(options.user)
                    inputline.extend(["-u", options.user])
                if options.password:
                    if options.encode:
                        options.password = Encryption.decode_credentials(options.password)
                    inputline.extend(["-p", options.password])
                if options.https_cert:
                    inputline.extend(["--https", options.https_cert])
            else:
                if self._rdmc.app.config.get_url():
                    inputline.extend([self._rdmc.app.config.get_url()])
                if self._rdmc.app.config.get_username():
                    inputline.extend(["-u", self._rdmc.app.config.get_username()])
                if self._rdmc.app.config.get_password():
                    inputline.extend(["-p", self._rdmc.app.config.get_password()])
                if self._rdmc.app.config.get_ssl_cert():
                    inputline.extend(["--https", self._rdmc.app.config.get_ssl_cert()])

        if inputline or not client:
            if not inputline:
                sys.stdout.write('Local login initiated...\n')
            self.lobobj.loginfunction(inputline)
        elif not client:
            raise InvalidCommandLineError("Please login or pass credentials" \
                                          " to complete the operation.")

    def definearguments(self, customparser):
        """ Wrapper function for new command main function

        :param customparser: command line input
        :type customparser: parser.
        """
        if not customparser:
            return

        add_login_arguments_group(customparser)

        customparser.add_argument(
            '--force',
            dest='force',
            help="Ignore any critical task checking and force disable iLO.",
            action="store_true",
            default=None,
        )
