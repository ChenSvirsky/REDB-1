from models import (Function, Description, String, Call,
                    Executable, Instruction, User, Graph)
from django.db.models.base import Model
from django.db.models.query import QuerySet


class FunctionWrapper:
    def __init__(self, attributes):
        for attr_name in attributes:
            setattr(self, attr_name, attributes[attr_name])

    def save(self):
        function, created = Function.objects.\
            get_or_create(signature=self.func_signature,
                          defaults={'args_size': self.args_size,
                                    'vars_size': self.vars_size,
                                    'regs_size': self.regs_size,
                                    'frame_size': self.frame_size,
                                    'num_of_strings': self.num_of_strings,
                                    'num_of_calls': self.num_of_calls,
                                    'num_of_insns': self.num_of_insns})

        if not created:
            return function

        ExecutableWrapper(self.exe_signature, function, self.exe_name).save()
        GraphWrapper(self.edges, self.blocks_bounds, self.num_of_blocks,
                     self.num_of_edges, function).save()

        instructions = []
        for offset in range(len(self.itypes)):
            str_offset = str(offset)
            immediate = None
            if str_offset in self.immediates:
                immediate = self.immediates[str_offset]
            string = None
            if str_offset in self.strings:
                string = StringWrapper(self.strings[str_offset]).save()
            call = None
            if str_offset in self.calls:
                call = \
                    CallWrapper(self.calls[str_offset]).save()
            instructions.\
                append(InstructionWrapper(self.itypes[offset],
                                          offset, function,
                                          immediate,
                                          string,
                                          call).instruction)

        # SQLite limitation
        chunks = [instructions[x:x + 100]
                  for x in xrange(0, len(instructions), 100)]
        for chunk in chunks:
            Instruction.objects.bulk_create(chunk)

        return function


class StringWrapper:
    def __init__(self, value):
        self.value = value

    def save(self):
        obj = String.objects.get_or_create(value=self.value)
        return obj[0]


class CallWrapper:
    def __init__(self, name):
        self.name = name

    def save(self):
        obj = Call.objects.get_or_create(name=self.name)
        return obj[0]


class GraphWrapper:
    def __init__(self, edges, blocks_bounds, num_of_blocks, num_of_edges,
                 function):
        self.edges = edges
        self.blocks_bounds = blocks_bounds
        self.num_of_blocks = num_of_blocks
        self.num_of_edges = num_of_edges
        self.function = function

    def save(self):
        return Graph.objects.create(edges=self.edges,
                                    blocks_bounds=self.blocks_bounds,
                                    num_of_blocks=self.num_of_blocks,
                                    num_of_edges=self.num_of_edges,
                                    function=self.function)


class ExecutableWrapper:
    def __init__(self, signature, function, exe_name):
        self.signature = signature
        self.function = function
        self.exe_name = exe_name

    def save(self):
        if not(self.signature == 'None'):
            exe, _ = Executable.objects.get_or_create(signature=self.signature)
            exe.functions.add(self.function)
            if self.exe_name not in exe.names:
                exe.names += self.exe_name + ", "
            exe.save()
            return exe


class InstructionWrapper:
    def __init__(self, itype, offset, function,
                 immediate=None, string=None, call=None):
        self.itype = itype
        self.offset = offset
        self.function = function
        self.immediate = immediate
        self.string = string
        self.call = call
        self.instruction = Instruction(function=self.function,
                                       itype=self.itype,
                                       offset=self.offset,
                                       immediate=self.immediate,
                                       string=self.string,
                                       call=self.call)


class DescriptionWrapper:
    def __init__(self, function_wrapper, description_data, user_name):
        self.function_wrapper = function_wrapper
        self.data = description_data
        self.user_name = user_name

    def save(self):
        user = User.objects.get(user_name=self.user_name)
        func = self.function_wrapper.save()

        try:
            desc = func.description_set.get(data=self.data)
        except Description.DoesNotExist:
            try:
                desc = func.description_set.get(user=user)
                desc.data = self.data
                desc.save()
            except Description.DoesNotExist:
                desc = Description.objects.create(data=self.data,
                                                  function=func,
                                                  user=user)
        return desc
