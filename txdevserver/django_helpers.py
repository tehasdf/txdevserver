import ast
import os


class DjangoSettingsModuleFinder(ast.NodeVisitor):
    django_settings_module = None

    def visit_Call(self, node):
        try:
            if (node.func.attr == 'setdefault' and
                node.args[0].s == 'DJANGO_SETTINGS_MODULE'):
                self.django_settings_module = node.args[1].s
                return
        except (IndexError, AttributeError):
            pass
        return self.generic_visit(node)


def get_django_app(manage_filename):
    with open(manage_filename) as f:
        manage_py_src = f.read()
    manage_py_ast = ast.parse(manage_py_src)
    finder = DjangoSettingsModuleFinder()
    finder.visit(manage_py_ast)

    if finder.django_settings_module is not None:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", finder.django_settings_module)
        import django.core.handlers.wsgi
        return django.core.handlers.wsgi.WSGIHandler()
    else:
        return None
