# -*- coding: utf-8 -*-

import os
import xml.dom.minidom
import sys
from kobo.client import ClientCommand

class BeakerCommand(ClientCommand):
    enabled = False
    conf_environ_key = 'BEAKER_CLIENT_CONF'

    if not os.environ.has_key(conf_environ_key):
        user_conf = os.path.expanduser('~/.beaker_client/config')
        old_conf = os.path.expanduser('~/.beaker')
        if os.path.exists(user_conf):
            conf = user_conf
        elif os.path.exists(old_conf):
            sys.stderr.write("%s is deprecated for config, please use %s instead\n" % (old_conf, 
                                                                                         user_conf))
            conf = old_conf
        else:
            conf = "/etc/beaker/client.conf"
        os.environ[conf_environ_key] = conf

class BeakerWorkflow(BeakerCommand):
    doc = xml.dom.minidom.Document()

    def options(self):
        """ Default options that all Workflows use """

        self.parser.add_option(
            "--debug",
            default=False,
            action="store_true",
            help="print the jobxml that it would submit",
        )
        self.parser.add_option(
            "--dryrun",
            default=False,
            action="store_true",
            help="Don't submit job to scheduler",
        )
        self.parser.add_option(
            "--arch",
            action="append",
            default=[],
            help="Include this Arch in job",
        )
        self.parser.add_option(
            "--distro",
            help="Use this Distro for job",
        )
        self.parser.add_option(
            "--family",
            help="Pick latest distro of this family for job",
        )
        self.parser.add_option(
            "--variant",
            help="Pick distro with this variant for job",
        )
        self.parser.add_option(
            "--machine",
            help="Require this machine for job",
        )
        self.parser.add_option(
            "--package",
            action="append",
            default=[],
            help="Include tests for Package in job",
        )
        self.parser.add_option(
            "--tag",
            action="append",
            default=[],
            help="Pick latest distro matching this tag for job",
        )
        self.parser.add_option(
            "--repo",
            action="append",
            default=[],
            help="Include this repo in job",
        )
        self.parser.add_option(
            "--task",
            action="append",
            default=[],
            help="Include this task in job",
        )
        self.parser.add_option(
            "--taskparams",
            action="append",
            default=[],
            help="Set task params 'name=value'",
        )
        self.parser.add_option(
            "--type",
            action="append",
            default=[],
            help="Include tasks of this type in job",
        )
        self.parser.add_option(
            "--keyvalues",
            action="append",
            default=[],
            help="Specify a system that matches these key/values",
        )
        self.parser.add_option(
            "--whiteboard",
            default="",
            help="Set the whiteboard for this job",
        )
        self.parser.add_option(
            "--nowait",
            default=False,
            action="store_true",
            help="Don't wait on job completion",
        )

    def getTasks(self, *args, **kwargs):
        """ get all requested tasks """

        tasks = list(args)
        #FIXME add tasks based on packages
        #FIXME add tasks based on task type
        tasks.extend([])
        return tasks

class BeakerBase(object):
    doc = xml.dom.minidom.Document()

    def toxml(self):
        """ return xml of job """
        return self.node.toprettyxml()

class BeakerJob(BeakerBase):
    def __init__(self, *args, **kwargs):
        self.node = self.doc.createElement('job')
        whiteboard = self.doc.createElement('whiteboard')
        whiteboard.appendChild(self.doc.createTextNode(kwargs.pop("whiteboard","")))
        self.node.appendChild(whiteboard)

    def addRecipeSet(self, recipeSet):
        """ properly add a recipeSet to this job """
        self.node.appendChild(recipeSet.node)

    def addRecipe(self, recipe):
        """ properly add a recipe to this job """
        recipeSet = self.doc.createElement('recipeSet')
        recipeSet.appendChild(recipe.node)
        self.node.appendChild(recipeSet)

class BeakerRecipeSet(BeakerBase):
    def __init__(self, *args, **kwargs):
        self.node = self.doc.createElement('recipeSet')

    def addRecipe(self, recipe):
        """ properly add a recipe to this recipeSet """
        self.node.appendChild(recipe.node)

class BeakerRecipe(BeakerBase):
    def __init__(self, *args, **kwargs):
        self.node = self.doc.createElement('recipe')
        self.andDistroRequires = self.doc.createElement('and')
        self.andHostRequires = self.doc.createElement('and')
        self.tasks = self.doc.createElement('tasks')
        distroRequires = self.doc.createElement('distroRequires')
        hostRequires = self.doc.createElement('hostRequires')
        distroRequires.appendChild(self.andDistroRequires)
        hostRequires.appendChild(self.andHostRequires)
        self.node.appendChild(distroRequires)
        self.node.appendChild(hostRequires)
        self.node.appendChild(self.tasks)

    def addBaseRequires(self, *args, **kwargs):
        """ Add base requires """
        distro = kwargs.get("distro", None)
        family = kwargs.get("family", None)
        tags = kwargs.get("tag", [])
        if distro:
            distroName = self.doc.createElement('distro_name')
            distroName.setAttribute('value', '%s' % distro)
            self.addDistroRequires(distroName)
        if family:
            distroFamily = self.doc.createElement('distro_family')
            distroFamily.setAttribute('value', '%s' % family)
            self.addDistroRequires(distroFamily)
        for tag in tags:
            distroTag = self.doc.createElement('distro_tag')
            distroTag.setAttribute('op', '=')
            distroTag.setAttribute('value', '%s' % tag)
            self.addDistroRequires(distroTag)

    def addHostRequires(self, node):
        self.andHostRequires.appendChild(node)

    def addDistroRequires(self, node):
        self.andDistroRequires.appendChild(node)

    def addTask(self, task, role='STANDALONE', paramNodes=[], taskParams=[]):
        recipeTask = self.doc.createElement('task')
        recipeTask.setAttribute('name', '%s' % task)
        recipeTask.setAttribute('role', '%s' % role)
        params = self.doc.createElement('params')
        for param in paramNodes:
            params.appendChild(param)
        for taskParam in taskParams:
            param = self.doc.createElement('param')
            param.setAttribute('name' , taskParam.split('=',1)[0])
            param.setAttribute('value' , taskParam.split('=',1)[1])
            params.appendChild(param)
        recipeTask.appendChild(params)
        self.tasks.appendChild(recipeTask)

