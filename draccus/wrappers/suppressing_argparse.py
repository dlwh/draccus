from argparse import ArgumentParser, _ArgumentGroup


class SuppressingArgumentParser(ArgumentParser):
    """
    ArgumentParser that has a slightly exotic method of handling conflicts.
    We don't want to raise an error if we have a conflict, we just want to ignore it.
    Ideally we'd have a way to say "take the first one", but that doesn't exist and
    can't be easily retrofitted. So we take the last one, but keep the
    old ones for the help message by leaving them in _group_actions but not in _actions.
    """

    def __init__(self, *args, **kwargs):
        kwargs = {**kwargs, "conflict_handler": "ignore"}
        super().__init__(*args, **kwargs)

    def add_argument_group(self, *args, **kwargs):
        group = _SuppressingArgumentGroup(self, *args, **kwargs)
        self._action_groups.append(group)
        return group

    def _handle_conflict_ignore(self, action, conflicting_actions):
        # remove all conflicting options
        for _option_string, action in conflicting_actions:
            action.container._remove_action(action)


class _SuppressingArgumentGroup(_ArgumentGroup):
    def __init__(self, container, *args, **kwargs):
        kwargs = {**kwargs, "conflict_handler": "ignore"}
        super().__init__(container, *args, **kwargs)

    def add_argument(self, *args, **kwargs):
        return super().add_argument(*args, **kwargs)

    def add_argument_group(self, *args, **kwargs):
        raise NotImplementedError("It's a bad idea to nest argument groups. argparse ignores them for help")

    def add_mutually_exclusive_group(self, *args, **kwargs):
        raise NotImplementedError("It's a bad idea to nest argument groups. argparse ignores them for help")

    def _remove_action(self, action):
        self._actions.remove(action)
        # don't remove from _group_actions, so that we can still show the old ones in the help message

    def _handle_conflict_ignore(self, action, conflicting_actions):
        # remove all conflicting options
        for _option_string, action in conflicting_actions:
            action.container._remove_action(action)
