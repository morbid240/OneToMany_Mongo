import datetime

from mongoengine import EmbeddedDocumentField

from Menu import Menu
from Option import Option


def prompt_for_date(prompt: str) -> datetime:
    """
    Prompts the user for a complete date/time.  This will keep prompting the user
    until they provide a valid date time stamp.
    ToDo - Allow the user to default to the current date & time to save time.
    :param prompt: The text to display when prompting the user for the date time stamp.
    :return: An instance of datetime.
    """
    print(prompt)
    valid = False
    while not valid:
        try:
            year: int = int(input('Enter year --> '))
            month: int = int(input('Enter month number --> '))
            day: int = int(input('Enter day number --> '))
            hour: int = int(input('Enter hour (24 hour clock) --> '))
            minute: int = int(input('Enter minute number --> '))
            second: int = int(input('Enter second number --> '))
            timestamp = datetime.datetime(year, month, day, hour, minute, second)
            return timestamp
        except ValueError as ve:
            print('Error on input: ', ve)
            print('Please try again.')


def get_attr_from_column(cls, column_name) -> str:
    """
    Returns the name of the attribute that corresponds to the given column name.  The attribute
    name is in CamelCase, while the column name is in snake_case.  The column within a Document
    class has the db_field property that gives us the database column name of that attribute.
    :param cls:             The class that has an attribute corresponding to the given column_name.
    :param column_name:     The column that we are looking for the corresponding attribute.
    :return:                THe name of the attribute for the given column.
    :history:               05/05/2024 - Updated to deal with embedded column.
    """
    first_dot: int = column_name.find('.')  # see if we have an embedded field.
    if first_dot > 0:  # we have a field that is embedded.
        first = column_name[:first_dot]  # get just the first field for now
        rest = column_name[first_dot + 1:]  # peel off the rest for next go around.
    else:
        first = column_name  # this is all that we have to do, no nesting past this.
    # loop through the cls OO attributes in the cls class, looking for the physical name provided.
    for attribute in cls.__dict__['_fields'].keys():
        # the 'id' attribute is a legitimate attribute with a db_name of _id, so we'll use it if need be.
        # if attribute != 'id':  # Skip the obligatory id field
        # Todo I'm not sure what happens with a dict or list attribute in the class.
        if getattr(cls, attribute).__dict__['db_field'] == first:  # Found the right attribute.
            if first_dot > 0:
                """getattr(cls, first) returns the attribute that corresponds to the given field.
                Then we get the document type from MongoEngine for that, which gives us the class it belongs to.
                Then we find the attribute name corresponding to the next column in line."""
                rest_attr = get_attr_from_column(getattr(cls, first).document_type, rest)
                return attribute + '.' + rest_attr
            else:
                return attribute


def select_general(cls):
    """Return one instance of the class that's supplied as an input, by prompting the user for
    the values of the selected uniqueness constraint for the collection corresponding to that class.
    :param cls: The class that the user wants a single instance of.
    :return: The instance that the user selected.
    :history:   05/07/2024 - Updated to use extract_attr instead of getattr to handle nested attributes."""
    # If we were doing this directly in mongodb, we'd say collection=db[whatever collection it is]
    collection = cls._get_collection()
    index_info = collection.index_information()
    # Loop through the indexes of the collection.
    choices = []
    for index in index_info.keys():
        # see if the index is unique.  If not, we're not interested in using it.
        # _id_ does not have a property named unique since _id_ is ALWAYS unique.  Hence, the order in the if statement.
        if index == '_id_' or index_info[index]['unique']:
            columns = [col[0] for col in index_info[index]['key']]
            choices.append(Option(f'index: {index} - cols: {columns}', index))
    index_menu = Menu('which index', 'Which index do you want to search by:', choices)
    while True:
        # What happens if there are no unique indexes at all?
        chosen_index = index_menu.menu_prompt()
        filters = {}  # The attribute/value pairs that we're going to search by
        for column in [col[0] for col in index_info[chosen_index]['key']]:
            # now I have to convert from the column name to the attribute name.
            attribute_name = get_attr_from_column(cls, column)
            # If this attribute is a reference, we need to go find that referenced document.
            attribute = extract_attr(cls, attribute_name)
            if type(attribute).__name__ == 'ReferenceField':
                # This attribute in this uniqueness requirement is a reference --> it's an identifying relationship.
                # Now we have to figure out the class that we're referencing.
                referenced_class = attribute.document_type
                # Use my general selection utility to find an instance of the referenced parent
                target = select_general(referenced_class)
                # and add the filter to point to the selected document in the parent collection.
                # I could have just said: filters[attribute_name] = select_general(attribute.document_type)
                # If the attribute is embedded, we need to make the '.' in the path to become a '__' for
                # MongoEngine.  Hopefully, we never have an attribute name with an embedded '.'
                field_name = attribute_name.replace('.', '__')
                filters[field_name] = target
                """This is intentionally recursive.  If A is a parent to B and B has a reference to A,
                and that reference is part of the uniqueness constraint in B that we are using to select 
                an instance of B, and B is a parent to C and C has a reference to B, and we want to select
                an instance of C based on the "migrated" reference to B, then you see where the 
                recursion comes in very handy."""
            elif type(attribute).__name__ == 'DateTimeField':
                field_name = attribute_name.replace('.', '__')
                filters[field_name] = prompt_for_date(f'search for {attribute_name} = --> ')
            elif type(attribute).__name__ == 'IntField':
                field_name = attribute_name.replace('.', '__')
                filters[field_name] = int(input(f'search for integer {attribute_name} = --> '))
            else:
                # It's not a reference, so prompt for the literal value.
                # This works for string and numeric, but honestly, I should convert the string depending on the type.
                # MongoEngine will search on nested attributes, but the . has to --> __
                field_name = attribute_name.replace('.', '__')
                filters[field_name] = input(f'search for {attribute_name} = --> ')
        # count the number of rows that meet that criteria.
        if cls.objects(**filters).count() == 1:
            return cls.objects(**filters).first()
        else:
            print('Sorry, no rows found that match those criteria.  Try again.')


def extract_attr(instance, attribute_name):
    """
    Return the value of an attribute from an instance of a class.  If the attribute is just a scalar in the class,
    then this just uses the Python getattr function.  But if the attribute is nested, that is, it's a field within
    an object within the class, then I have to extract the value from that embedded object.  Obviously, this could
    be recursive.
    :param instance:        The object that has the attribute that you need the value for.
    :param attribute_name:  The name of the attribute.  Nested attributes will use the dot notation to specify
                            the path to the attribute.  For instance, department.departmentRef indicates that
                            departmentRef is a field within the department object within the instance object.
    :return:                Either the attribute itself (if instance is a class) or the value of the attribute
                            if instance is an object.
    """
    first_dot: int = attribute_name.find('.')  # see if we have an embedded field.
    if first_dot < 0:  # This is the terminal case.  We're done.
        if isinstance(instance, EmbeddedDocumentField):
            return getattr(instance.document_type, attribute_name)
        else:
            return getattr(instance, attribute_name)
    else:
        first = attribute_name[:first_dot]  # Find the name of the class that the field is embedded into.
        rest = attribute_name[first_dot + 1:]  # Get the attribute name within that embedded class.
        # Go one level deeper into the nested objects to get the attribute value.
        # The document type is a property of EmbeddedDocumentField that gives us the CLASS.
        if isinstance(instance, EmbeddedDocumentField):
            return extract_attr(getattr(instance.document_type, first), rest)
        else:
            return extract_attr(getattr(instance, first), rest)


def unique_general(instance):
    """
    Check all uniqueness constraints on the collection that instance belongs to and return those
    uniqueness constraints that have been violated.  If that returned list has no members, then
    the instance does not duplicate any documents already in the collection, and it is safe to
    save that instance.
    :param instance:    An instance of a MongoEngine class that the user want to test against all
                        uniqueness constraints on that collection.
    :return:            A list of the 0 or more uniqueness constraints that have been violated.
    """
    # If we were doing this directly in mongodb, we'd say collection=db[whatever collection it is]
    cls = instance.__class__  # get the class from the instance.
    collection = cls._get_collection()  # Get the collection corresponding to that class.
    index_info = collection.index_information()  # get a list of all indexes on that collection.
    # Loop through the indexes of the collection.
    constraints = []
    violated_constraints = []
    for index in index_info.keys():  # Loop through the list of index names.
        # see if the index is unique.  If not, we're not interested in using it.
        # _id_ does not have a property named unique since _id_ is ALWAYS unique.
        # Normally, _id_ is assigned by MongoDB, but the user COULD use that for a descriptive
        # attribute, which COULD mean that there is a document with that _id_ value already.
        if index == '_id_' or index_info[index]['unique']:
            # harvest the list of column names from this index.
            columns = [col[0] for col in index_info[index]['key']]
            # add the name of the index & the column list to our constraints list of dictionaries.
            constraints.append({'name': index, 'columns': columns})
    for constraint in constraints:
        # What happens if there are no unique indexes at all?
        filters = {}  # The attribute/value pairs that we're going to search by
        for column in constraint['columns']:
            # now I have to convert from the column name to the attribute name.
            attribute_name = get_attr_from_column(cls, column)
            # Add the next key=value pair to our list of filters.
            # MongoEngine requires that the '.' be replaced by a __ in the field reference.
            field_name = attribute_name.replace('.', '__')
            filters[field_name] = extract_attr(instance, attribute_name)  # instance[attribute_name]
        # count the number of rows that meet those criteria.
        if cls.objects(**filters).count() == 1:
            # there is a document in the collection that matches the supplied instance on all attributes
            # of this uniqueness constraint.  So we have another uniqueness constraint violation.
            violated_constraints.append(constraint)
    # If the returned list of violated constraints == [], we know that we are good to insert this object.
    return violated_constraints
