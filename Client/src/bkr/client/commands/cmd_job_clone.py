# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

"""
bkr job-clone: Clone existing Beaker jobs
=========================================

.. program:: bkr job-clone

Synopsis
--------

| :program:`bkr job-clone` [*options*]
|       [--wait] [--dry-run] [--xml] [--pretty-xml] <taskspec>...

Description
-----------

Specify one or more <taskspec> arguments to be cloned. A new job will be 
created for each argument. The cloned job ids will be printed to stdout.

The <taskspec> arguments follow the same format as in other :program:`bkr` 
subcommands (for example, ``J:1234``). See :ref:`Specifying tasks <taskspec>` 
in :manpage:`bkr(1)`.

Only jobs and recipe sets may be cloned.

Options
-------

.. option:: --wait

   When this option is given, the command will not terminate until the clone
   job has finished running.

.. option:: --xml

   Print the job XML before submitting it.

.. option:: --pretty-xml

   Print the job XML in a easily readable format before submitting it.

.. option:: --dry-run

   Run through the job-clone process without actually submitting the cloned job

.. option:: --job-owner <username>

   Clone the job on behalf of <username>. The cloned job will be owned by
   <username> rather than the cloning user.

   The cloning user must be a submission delegate of <username>. Users can
   add other users as submission delegates on their :guilabel:`Preferences`
   page in Beaker's web UI.



Common :program:`bkr` options are described in the :ref:`Options 
<common-options>` section of :manpage:`bkr(1)`.

Exit status
-----------

Non-zero on error, otherwise zero.
A failure in cloning *any* of the arguments is considered to be an error, and 
the exit status will be 1.

Examples
--------

Clone job 1234 and wait for it to finish::

    bkr job-clone --wait J:1234

See also
--------

:manpage:`bkr(1)`
"""

import sys
import lxml.etree
from bkr.client import BeakerCommand
from optparse import OptionValueError
from bkr.client.task_watcher import *

class Job_Clone(BeakerCommand):
    """Clone Jobs/RecipeSets"""
    enabled = True

    def options(self):
        self.parser.usage = "%%prog %s [options] <taskspec>..." % self.normalized_name
        self.parser.add_option(
            "--wait",
            default=False,
            action="store_true",
            help="wait on job completion",
        )
        self.parser.add_option(
            "--dry-run", "--dryrun",
            dest="dryrun",
            default=False,
            action="store_true",
            help="Test the likely output of job-clone without cloning anything",
        )
        self.parser.add_option(
            "--xml",
            default=False,
            action="store_true",
            help="print the jobxml that it would submit",
        )
        self.parser.add_option(
            "--pretty-xml", "--prettyxml",
            dest="prettyxml",
            action="store_true",
            default=False,
            help="print the jobxml that it would submit, in pretty format",
        )
        self.parser.add_option(
             '--job-owner', metavar='USERNAME',
             help='Clone job on behalf of USERNAME '
                  '(cloning user must be a submission delegate for job owner)',
        )

    def run(self, *args, **kwargs):
        self.check_taskspec_args(args, permitted_types=['J', 'RS'])

        wait = kwargs.pop("wait", None)
        xml = kwargs.pop("xml", None)
        pretty = kwargs.pop("prettyxml", False)
        dryrun = kwargs.pop("dryrun", None)
        job_owner = kwargs.pop("job_owner", None)

        if len(args) < 1:
            self.parser.error('Please specify a job or recipeset to clone')

        submitted_jobs = []
        failed = False
        clone = True
        self.set_hub(**kwargs)
        for task in args:
            try:
                task_type, task_id = task.split(":")
                if task_type.upper() == 'RS':
                    from_job = False
                else:
                    from_job = True
                jobxml = self.hub.taskactions.to_xml(task, clone, from_job)
                # XML is really bytes, the fact that the server is sending the bytes as an
                # XML-RPC Unicode string is just a mistake in Beaker's API
                jobxml = jobxml.encode('utf8')
                if job_owner is not None:
                    # root is job tag
                    root = lxml.etree.fromstring(jobxml)
                    root.set('user', job_owner)
                    jobxml = lxml.etree.tostring(root, encoding='utf8')
                if xml or pretty:
                    print lxml.etree.tostring(lxml.etree.fromstring(jobxml),
                                            pretty_print=pretty,
                                            xml_declaration=True,
                                            encoding='utf8')
                if not dryrun:
                    submitted_jobs.append(self.hub.jobs.upload(jobxml))
            except Exception, ex:
                failed = True
                raise
                print >>sys.stderr, ex
        if not dryrun:
            print "Submitted: %s" % submitted_jobs
            if wait:
                watch_tasks(self.hub, submitted_jobs)
        if failed:
            sys.exit(1)
