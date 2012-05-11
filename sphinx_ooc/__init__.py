import re
from sphinx import addnodes
from sphinx.domains import Domain, ObjType
from sphinx.locale import l_, _
from sphinx.directives import ObjectDescription
from sphinx.roles import XRefRole
from sphinx.util.nodes import make_refnode
from sphinx.util.docfields import Field, GroupedField, TypedField

ooc_sig_re = re.compile(
    r'''^ ([\w<>/,]*[ /])?            # class name(s)
          ([\w<>~,]+)  \s*             # thing name
          (?: \((.*)\))?           # optional: arguments
          (?:\s* -> \s* (.*))?  #           return annotation
          $                   # and nothing more
          ''', re.VERBOSE)
ooc_paramlist_re = re.compile(r'([\[\],])')  # split at '[', ']' and ','

class OOCObject(ObjectDescription):
    has_arguments = False
    display_prefix = None

    def get_signature_prefix(self, sig):
        return ''

    def parse_arglist(self, parameternode, arglist):
        """
            Parse and create a parameter list. With crossrefs even!
        """
        stack = [parameternode]
        token_before = None
        for token in ooc_paramlist_re.split(arglist):
            if token_before is not None:
                if token == ',':
                    # add commas yay.
                    token_before += token
                    continue
                else:
                    token = token_before + token
                    print 'NOW TOKEN: %r' % token
                    token_before = None
            if token.count('<') != token.count('>'):
                # splitted in the middle of a <A, B, C> declaration :(
                token_before = token
            elif not token or token == ',' or token.isspace():
                pass
            else:
                token = token.strip()
            if ':' in token:
                # We have a type and we can link it.
                stack[-1] += addnodes.desc_parameter('', '', *self._resolve_typeref(token))
            else:
                stack[-1] += addnodes.desc_parameter(token, token)

    def _resolve_typeref(self, text):
        return self.state.inline_text(text, self.lineno)[0]

    def handle_signature(self, sig, signode):
        """
            Parse the object (or function) signature and create the corresponding nodes.
        """
        match = ooc_sig_re.match(sig)
        if match is None:
            raise ValueError
        name_prefix, name, arglist, retann = match.groups()
        classname = name_prefix
        if self.env.temp_data.get('ooc:class'):
            # TODO!
            raise NotImplementedError()
        else:
            add_module = True
            fullname = classname and classname + name or name

        prefix = self.get_signature_prefix(sig)
        if prefix:
            signode += addnodes.desc_annotation(prefix, prefix)
        #if classname:
        #   signode += addnodes.desc_addname(classname, classname)

        # exceptions are a special case, since they are documented in the
        # 'exceptions' module.
        elif add_module and self.env.config.add_module_names:
            modname = self.options.get('module', self.env.currmodule)
            if modname and modname != 'exceptions':
                nodetext = modname + '/'
                # signode += addnodes.desc_addname(nodetext, nodetext)

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
            signode += addnodes.desc_addname(name_prefix + '.', name_prefix + '.')
        signode += addnodes.desc_name(name, name)
        if self.has_arguments:
            parameterlist = addnodes.desc_parameterlist()
            signode += parameterlist
            if arglist:
                self.parse_arglist(parameterlist, arglist)
            print parameterlist

        return fullname, name_prefix

    def add_target_and_index(self, name_obj, sig, signode):
        objectname = self.options.get(
            'object', self.env.temp_data.get('ooc:object'))
        fullname = name_obj[0]
        if fullname not in self.state.document.ids:
            signode['names'].append(fullname)
            signode['ids'].append(fullname)
            signode['first'] = not self.names
            self.state.document.note_explicit_target(signode)
            objects = self.env.domaindata['ooc']['objects']
            if fullname in objects:
                self.state_machine.reporter.warning(
                    'duplicate object description of %s, ' % fullname +
                    'other instance in ' +
                    self.env.doc2path(objects[fullname][0]),
                    line=self.lineno)
            objects[fullname] = self.env.docname, self.objtype

        indextext = self.get_index_text(objectname, name_obj)
        if indextext:
            self.indexnode['entries'].append(('single', indextext,
                                              fullname,
                                              ''))

    def get_index_text(self, objectname, name_obj):
        name, obj = name_obj
        if self.objtype == 'function':
            if not obj:
                return _('%s() (built-in function)') % name
            return _('%s() (%s method)') % (name, obj)
        elif self.objtype == 'class':
            return _('%s() (class)') % name
        elif self.objtype == 'data':
            return _('%s (global variable or constant)') % name
        elif self.objtype == 'attribute':
            return _('%s (%s attribute)') % (name, obj)
        return ''


class OOCCallable(OOCObject):
    has_arguments = True
    doc_field_types = [
#        TypedField('arguments', label=l_('Arguments'),
#                   names=('argument', 'arg', 'parameter', 'param'),
#                   typerolename='func', typenames=('paramtype', 'type')),
#        GroupedField('errors', label=l_('Throws'), rolename='err',
#                     names=('throws', ),
#                     can_collapse=True),
        Field('returnvalue', label=l_('Returns'), has_arg=False,
              names=('returns', 'return')),
        Field('returntype', label=l_('Return type'), has_arg=False,
              names=('rtype',)),
    ]

class OOCDomain(Domain):
    name = 'ooc'
    label = 'ooc'
    object_types = {
        'function': ObjType(l_('function'), 'func'),
    }
    directives = {
        'function': OOCCallable
    }
    initial_data = {
        'objects': {}, # fullname -> docname, objtype
    }

    def __init__(self, env):
        Domain.__init__(self, env)

    def clear_doc(self, docname):
        for fullname, (fn, _) in self.data['objects'].items():
            if fn == docname:
                del self.data['objects'][fullname]

    def find_obj(self, env, obj, name, typ, searchorder=0):
        if name[-2:] == '()':
            name = name[:-2]
        objects = self.data['objects']
        newname = None
        if searchorder == 1:
            if obj and obj + '.' + name in objects:
                newname = obj + '.' + name
            else:
                newname = name
        else:
            if name in objects:
                newname = name
            elif obj and obj + '.' + name in objects:
                newname = obj + '.' + name
        return newname, objects.get(newname)

    def resolve_xref(self, env, fromdocname, builder, typ, target, node,
                     contnode):
        objectname = node.get('ooc:object')
        searchorder = node.hasattr('refspecific') and 1 or 0
        name, obj = self.find_obj(env, objectname, target, typ, searchorder)
        if not obj:
            return None
        return make_refnode(builder, fromdocname, obj[0],
                            name.replace('$', '_S_'), contnode, name)

    def get_objects(self):
        for refname, (docname, type) in self.data['objects'].iteritems():
            yield refname, refname, type, docname, \
                  refname.replace('$', '_S_'), 1
def setup(app):
    app.add_domain(OOCDomain)
