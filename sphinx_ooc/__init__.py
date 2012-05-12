import re

from docutils import nodes
from docutils.parsers.rst import directives

from sphinx import addnodes
from sphinx.domains import Domain, ObjType
from sphinx.locale import l_, _
from sphinx.directives import ObjectDescription
from sphinx.roles import XRefRole
from sphinx.util.nodes import make_refnode
from sphinx.util.compat import Directive
from sphinx.util.docfields import Field, GroupedField, TypedField

ooc_sig_re = re.compile(
    r'''^ ([\w<>/,]*[ /])?            # class name(s)
          ([\w<>~,?!]+)  \s*             # thing name
          (?: \((.*)\))?           # optional: arguments
          (?:\s* -> \s* (.*))?  #           return annotation
          $                   # and nothing more
          ''', re.VERBOSE)
ooc_paramlist_re = re.compile(r'([\[\],])')  # split at '[', ']' and ','

class OOCXRefRole(XRefRole):
    def process_link(self, env, refnode, has_explicit_title, title, target):
        refnode['ooc:module'] = env.temp_data.get('ooc:module')
        refnode['ooc:class'] = env.temp_data.get('ooc:class')
        if not has_explicit_title:
            title = title.lstrip('.')   # only has a meaning for the target
            target = target.lstrip('~') # only has a meaning for the title
            # if the first character is a tilde, don't display the module/class
            # parts of the contents
            if title[0:1] == '~':
                title = title[1:]
                dot = title.rfind(' ')
                if dot != -1:
                    title = title[dot+1:]
        # if the first character is a dot, search more specific namespaces first
        # else search builtins first
        if target[0:1] == ' ':
            target = target[1:]
            refnode['refspecific'] = True
        return title, target

class OOCObject(ObjectDescription):
    has_arguments = False
    display_prefix = None

    def get_signature_prefix(self, sig):
        return ''

    def parse_arglist(self, parameternode, arglist):
        """
            Parse and create a parameter list. With crossrefs even!
        """
        # TODO: do a real parser that handles nested function types with argument lists
        # e.g. `f: func (b: Func (a, b, c) -> d)`
        stack = [parameternode]
        token_before = None
        openparens = 0
        for token in ooc_paramlist_re.split(arglist):
            if token == ',':
                # skip lonely commas. we don't want them. :(
                continue
            if token_before is not None:
                if token == ',':
                    # add commas yay.
                    token_before += token
                    continue
                else:
                    token = token_before + token
                    token_before = None
            openparens += token.count('(')
            openparens -= token.count(')')
            if token.count('<') != (token.count('>') - token.count('->')):
                # splitted in the middle of a <A, B, C> declaration :(
                token_before = token
                continue
            if openparens > 0:
                # we still have some open parens! we need to join the next token
                token_before = token + ', ' # TODO: I guess?
                # but reset the counter
                openparens -= token.count('(')
                openparens += token.count(')')
                continue
            elif not token or token == ',' or token.isspace():
                continue
            else:
                token = token.strip()
            if ':' in token:
                # We have a type and we can link it.
                if '->:' in token:
                    token = token.replace('->:', '-> :') # TODO: wow, how nasty
                stack[-1] += addnodes.desc_parameter('', '', *self._resolve_typeref(token))
            else:
                stack[-1] += addnodes.desc_parameter(token, token)

    def _resolve_typeref(self, text):
        # '*' is not really emphasis, but a pointer.
        return self.state.inline_text(text.replace('*', r'\*'), self.lineno)[0]

    def before_content(self):
        # needed for automatic qualification of members (reset in subclasses)
        self.clsname_set = False

    def after_content(self):
        if self.clsname_set:
            self.env.temp_data['ooc:class'] = None

    def handle_signature(self, sig, signode):
        """
            Parse the object (or function) signature and create the corresponding nodes.
        """
        match = ooc_sig_re.match(sig)
        if match is None:
            raise ValueError

        name_prefix, name, arglist, retann = match.groups()

        # determine module and class name (if applicable), as well as full name
        modname = self.options.get(
            'module', self.env.temp_data.get('ooc:module'))
        classname = self.env.temp_data.get('ooc:class')
        if classname:
            add_module = False
            if name_prefix and name_prefix.startswith(classname):
                fullname = name_prefix + name
                # class name is given again in the signature
                name_prefix = name_prefix[len(classname):].lstrip(' ')
            elif name_prefix:
                # class name is given in the signature, but different
                # (shouldn't happen)
                fullname = classname + ' ' + name_prefix + name
            else:
                # class name is not given in the signature
                fullname = classname + ' ' + name
        else:
            add_module = True
            if name_prefix:
                classname = name_prefix.rstrip(' ')
                fullname = name_prefix + name
            else:
                classname = ''
                fullname = name
        signode['module'] = modname
        signode['class'] = classname
        signode['fullname'] = fullname

        sig_prefix = self.get_signature_prefix(sig)
        if sig_prefix:
            signode += addnodes.desc_annotation(sig_prefix, sig_prefix)

        if name_prefix:
            signode += addnodes.desc_addname(name_prefix, name_prefix)
#        if not arglist:
#            if self.needs_arglist():
#                # for callables, add an empty parameter list
#                signode += addnodes.desc_parameterlist()
#            if retann:
#                signode += addnodes.desc_returns('', '', *self._resolve_typeref(retann))
#            return fullname, classname

        if self.display_prefix:
            signode += addnodes.desc_annotation(self.display_prefix,
                                                self.display_prefix)
        if name_prefix:
            signode += addnodes.desc_addname(name_prefix + ' ', name_prefix + ' ')
        signode += addnodes.desc_name(name, name)

        if self.needs_arglist():
            parameterlist = addnodes.desc_parameterlist()
            signode += parameterlist
            if arglist:
                self.parse_arglist(parameterlist, arglist)

        return fullname, name_prefix

    def needs_arglist(self):
        return False

    def add_target_and_index(self, name_cls, sig, signode):
        modname = self.options.get(
            'module', self.env.temp_data.get('ooc:module'))
        fullname = (modname and modname + ' ' or '') + name_cls[0]
        # note target
        if fullname not in self.state.document.ids:
            signode['names'].append(fullname)
            signode['ids'].append(fullname)
            signode['first'] = (not self.names)
            self.state.document.note_explicit_target(signode)
            objects = self.env.domaindata['ooc']['objects']
            if fullname in objects:
                self.state_machine.reporter.warning(
                    'duplicate object description of %s, ' % fullname +
                    'other instance in ' +
                    self.env.doc2path(objects[fullname][0]) +
                    ', use :noindex: for one of them',
                    line=self.lineno)
            objects[fullname] = (self.env.docname, self.objtype)

        indextext = self.get_index_text(modname, name_cls)
        if indextext:
            self.indexnode['entries'].append(('single', indextext,
                                              fullname, ''))
class OOCModulelevel(OOCObject):
    doc_field_types = [
        TypedField('parameter', label=l_('Parameters'),
                   names=('param', 'parameter', 'arg', 'argument',
                          'keyword', 'kwarg', 'kwparam'),
                   typerolename='obj', typenames=('paramtype', 'type'),
                   can_collapse=True),
        TypedField('variable', label=l_('Variables'), rolename='obj',
                   names=('var', 'ivar', 'cvar'),
                   typerolename='obj', typenames=('vartype',),
                   can_collapse=True),
        GroupedField('exceptions', label=l_('Raises'), rolename='exc',
                     names=('raises', 'raise', 'exception', 'except'),
                     can_collapse=True),
        Field('returnvalue', label=l_('Returns'), has_arg=False,
              names=('returns', 'return')),
        Field('returntype', label=l_('Return type'), has_arg=False,
              names=('rtype',)),
    ]

    def needs_arglist(self):
        return self.objtype == 'function'

    def get_index_text(self, modname, name_cls):
        if self.objtype == 'function':
            if not modname:
                return _('%s() (built-in function)') % name_cls[0]
            return _('%s() (in module %s)') % (name_cls[0], modname)
        elif self.objtype == 'data':
            if not modname:
                return _('%s (built-in variable)') % name_cls[0]
            return _('%s (in module %s)') % (name_cls[0], modname)
        else:
            return ''

class OOCClasslike(OOCObject):
    def get_signature_prefix(self, sig):
        return self.objtype + ' '

    def get_index_text(self, modname, name_cls):
        if self.objtype == 'class':
            if not modname:
                return l_('%s (built-in class)') % name_cls[0]
            return _('%s (class in %s)') % (name_cls[0], modname)
        elif self.objtype == 'cover':
            if not modname:
                return l_('%s (built-in cover)') % name_clas[0]
            return _('%s (cover in %s)') % (name_cls[0], modname)
        else:
            return ''

    def before_content(self):
        OOCObject.before_content(self)
        if self.names:
            self.env.temp_data['ooc:class'] = self.names[0][0]
            self.clsname_set = True

class OOCModule(Directive):
    """
    Directive to mark description of a new module.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'platform': lambda x: x,
        'synopsis': lambda x: x,
        'noindex': directives.flag,
        'deprecated': directives.flag,
    }

    def run(self):
        env = self.state.document.settings.env
        modname = self.arguments[0].strip()
        noindex = 'noindex' in self.options
        env.temp_data['ooc:module'] = modname
        ret = []
        if not noindex:
            env.domaindata['ooc']['modules'][modname] = \
                (env.docname, self.options.get('synopsis', ''),
                 self.options.get('platform', ''), 'deprecated' in self.options)
            # make a duplicate entry in 'objects' to facilitate searching for
            # the module in PythonDomain.find_obj()
            env.domaindata['ooc']['objects'][modname] = (env.docname, 'module')
            targetnode = nodes.target('', '', ids=['module-' + modname],
                                      ismod=True)
            self.state.document.note_explicit_target(targetnode)
            # the platform and synopsis aren't printed; in fact, they are only
            # used in the modindex currently
            ret.append(targetnode)
            indextext = _('%s (module)') % modname
            inode = addnodes.index(entries=[('single', indextext,
                                             'module-' + modname, '')])
            ret.append(inode)
        return ret

class OOCClassmember(OOCObject):
    def needs_arglist(self):
        return self.objtype.endswith('method')

    def get_signature_prefix(self, sig):
        if self.objtype == 'staticmethod':
            return 'static '
        elif self.objtype == 'classmethod':
            return 'classmethod '
        return ''

    def get_index_text(self, modname, name_cls):
        name, cls = name_cls
        add_modules = self.env.config.add_module_names
        if self.objtype == 'method':
            try:
                clsname, methname = name.rsplit('.', 1)
            except ValueError:
                if modname:
                    return _('%s() (in module %s)') % (name, modname)
                else:
                    return '%s()' % name
            if modname and add_modules:
                return _('%s() (%s.%s method)') % (methname, modname, clsname)
            else:
                return _('%s() (%s method)') % (methname, clsname)
        elif self.objtype == 'staticmethod':
            try:
                clsname, methname = name.rsplit('.', 1)
            except ValueError:
                if modname:
                    return _('%s() (in module %s)') % (name, modname)
                else:
                    return '%s()' % name
            if modname and add_modules:
                return _('%s() (%s.%s static method)') % (methname, modname,
                                                          clsname)
            else:
                return _('%s() (%s static method)') % (methname, clsname)
        elif self.objtype == 'classmethod':
            try:
                clsname, methname = name.rsplit('.', 1)
            except ValueError:
                if modname:
                    return _('%s() (in module %s)') % (name, modname)
                else:
                    return '%s()' % name
            if modname:
                return _('%s() (%s.%s class method)') % (methname, modname,
                                                         clsname)
            else:
                return _('%s() (%s class method)') % (methname, clsname)
        elif self.objtype == 'attribute':
            try:
                clsname, attrname = name.rsplit('.', 1)
            except ValueError:
                if modname:
                    return _('%s (in module %s)') % (name, modname)
                else:
                    return name
            if modname and add_modules:
                return _('%s (%s.%s attribute)') % (attrname, modname, clsname)
            else:
                return _('%s (%s attribute)') % (attrname, clsname)
        else:
            return ''

    def before_content(self):
        OOCObject.before_content(self)
        lastname = self.names and self.names[-1][1]
        if lastname and not self.env.temp_data.get('ooc:class'):
            self.env.temp_data['ooc:class'] = lastname.strip('.')
            self.clsname_set = True


class OOCDomain(Domain):
    name = 'ooc'
    label = 'ooc'
    object_types = {
        'function': ObjType(l_('function'), 'func', 'obj'),
        'module': ObjType(l_('module'), 'mod', 'obj'),
        'class': ObjType(l_('class'), 'class', 'obj'),
        'cover': ObjType(l_('cover'), 'cover', 'obj'),
        'method':       ObjType(l_('method'),        'meth', 'obj'),
        'classmethod':  ObjType(l_('class method'),  'meth', 'obj'),
        'staticmethod': ObjType(l_('static method'), 'meth', 'obj'),
        'attribute':    ObjType(l_('attribute'),     'attr', 'obj'),
        'field':         ObjType(l_('field'),          'field', 'obj'),
        'data':         ObjType(l_('data'),          'data', 'obj'),
        'enum': ObjType(l_('enum'), 'enum', 'obj'),
     }
    directives = {
        'function': OOCModulelevel,
        'module': OOCModule,
        'class': OOCClasslike,
        'cover': OOCClasslike,
        'var': OOCModulelevel,
        'method':          OOCClassmember,
        'classmethod':     OOCClassmember,
        'staticmethod':    OOCClassmember,
        'field':       OOCClassmember,
        'enum': OOCClasslike,
    }
    roles = {
        'func': OOCXRefRole(fix_parens=True),
        'mod': OOCXRefRole(),
        'cover': OOCXRefRole(),
        'class': OOCXRefRole(),
        'const': OOCXRefRole(),
        'field':  OOCXRefRole(),
        'meth':  OOCXRefRole(fix_parens=True),
        'mod':   OOCXRefRole(),
        'obj':   OOCXRefRole(),
        'var': OOCXRefRole(),
        'enum': OOCXRefRole(),
    }
    initial_data = {
        'objects': {},  # fullname -> docname, objtype
        'modules': {},  # modname -> docname, synopsis, platform, deprecated
    }

    def __init__(self, env):
        Domain.__init__(self, env)

    def clear_doc(self, docname):
        for fullname, (fn, _) in self.data['objects'].items():
            if fn == docname:
                del self.data['objects'][fullname]

    def find_obj(self, env, modname, classname, name, type, searchmode=0):
        """Find a Python object for "name", perhaps using the given module
        and/or classname.  Returns a list of (name, object entry) tuples.
        """
        # skip parens
        if name[-2:] == '()':
            name = name[:-2]

        if not name:
            return []

        objects = self.data['objects']
        matches = []

        newname = None
        if searchmode == 1:
            objtypes = self.objtypes_for_role(type)
            if objtypes is not None:
                if modname and classname:
                    fullname = modname + ' ' + classname + ' ' + name
                    if fullname in objects and objects[fullname][1] in objtypes:
                        newname = fullname
                if not newname:
                    if modname and modname + ' ' + name in objects and \
                       objects[modname + ' ' + name][1] in objtypes:
                        newname = modname + ' ' + name
                    elif name in objects and objects[name][1] in objtypes:
                        newname = name
                    else:
                        # "fuzzy" searching mode
                        searchname = ' ' + name
                        matches = [(oname, objects[oname]) for oname in objects
                                   if oname.endswith(searchname)
                                   and objects[oname][1] in objtypes]
        else:
            # NOTE: searching for exact match, object type is not considered
            if name in objects:
                newname = name
            elif type == 'mod':
                # only exact matches allowed for modules
                return []
            elif classname and classname + ' ' + name in objects:
                newname = classname + ' ' + name
            elif modname and modname + ' ' + name in objects:
                newname = modname + ' ' + name
            elif modname and classname and \
                     modname + ' ' + classname + ' ' + name in objects:
                newname = modname + ' ' + classname + ' ' + name
            # special case: object methods
            elif type in ('func', 'meth') and ' ' not in name and \
                 'object.' + name in objects:
                newname = 'object.' + name
        if newname is not None:
            matches.append((newname, objects[newname]))
        return matches

    def resolve_xref(self, env, fromdocname, builder,
                     type, target, node, contnode):
        modname = node.get('ooc:module')
        clsname = node.get('ooc:class')
        searchmode = node.hasattr('refspecific') and 1 or 0
        matches = self.find_obj(env, modname, clsname, target,
                                type, searchmode)
        if not matches:
            return None
        elif len(matches) > 1:
            env.warn_node(
                'more than one target found for cross-reference '
                '%r: %s' % (target, ', '.join(match[0] for match in matches)),
                node)
        name, obj = matches[0]

        if obj[1] == 'module':
            # get additional info for modules
            docname, synopsis, platform, deprecated = self.data['modules'][name]
            assert docname == obj[0]
            title = name
            if synopsis:
                title += ': ' + synopsis
            if deprecated:
                title += _(' (deprecated)')
            if platform:
                title += ' (' + platform + ')'
            return make_refnode(builder, fromdocname, docname,
                                'module-' + name, contnode, title)
        else:
            return make_refnode(builder, fromdocname, obj[0], name,
                                contnode, name)

    def get_objects(self):
        for modname, info in self.data['modules'].iteritems():
            yield (modname, modname, 'module', info[0], 'module-' + modname, 0)
        for refname, (docname, type) in self.data['objects'].iteritems():
            yield (refname, refname, type, docname, refname, 1)

def setup(app):
    app.add_domain(OOCDomain)
