import inspect
import json


def introspection_query(depth: int):
    fields_query = 'kind name ofType {' * depth + 'kind name' + '}' * depth
    return inspect.cleandoc(
        '''{
            __schema {
                types {
                    kind
                    name
                    fields {
                        name
                        type {
                            ''' + fields_query + '''
                        }
                    }
                }
            }
        }'''
    )


def _resolve_type(types_by_name, graphql_type):
    crumbs = []

    while True:
        crumbs.append(graphql_type)
        if len(crumbs) >= 99:
            crumbs_repr = '\n'.join(
                f'{i}. {json.dumps(crumb)}' for i, crumb in enumerate(crumbs, start=1))

            assert len(crumbs) < 99, f'Aborting actualization (closed loop?)\nStack:\n{crumbs_repr}'

        if graphql_type['kind'] in ('LIST', 'NON_NULL'):
            graphql_type = graphql_type['ofType']
            continue

        if 'ofType' in graphql_type and graphql_type['ofType'] is None and graphql_type.get('name'):
            # Named reference to some other type
            referenced_name = graphql_type['name']
            referenced_type = types_by_name.get(referenced_name)
            assert referenced_type, f'Cannot resolve type name {referenced_name}'
            graphql_type = referenced_type
            continue

        if graphql_type['kind'] == 'UNION':
            return graphql_type

        return graphql_type


def _craft_complete_query(types_by_name, visited_types, graphql_type, allow_recursive, indent=''):
    graphql_type = _resolve_type(types_by_name, graphql_type)

    if graphql_type in visited_types:
        return '# Skipping already visited type'

    kind = graphql_type['kind']
    if kind == 'SCALAR':
        return ''
    elif kind == 'ENUM':
        return '# Skipping enum'
    elif kind == 'UNION':
        return '# Skipping union'
    elif kind == 'INTERFACE':
        return '# Skipping interface'
    elif kind == 'OBJECT':
        visited_types.append(graphql_type)
        fields = sorted(graphql_type['fields'], key=lambda t: t['name'])
        return '{\n' + '\n'.join(
            (f'{indent}  {field["name"]} ' + _craft_complete_query(
                types_by_name, visited_types[:] if allow_recursive else visited_types,
                field['type'], allow_recursive, indent + '  '
            ))
            for field in fields
        ) + '\n' + indent + '}'
    else:
        raise ValueError(f'Unsupported GraphQL kind {kind}')


def complete_query(schema_doc: dict, root_name: str, allow_recursive=True) -> str:
    types_by_name = {}
    for graphql_type in schema_doc['__schema']['types']:
        types_by_name[graphql_type['name']] = graphql_type

    return _craft_complete_query(types_by_name, [], types_by_name[root_name], allow_recursive)
