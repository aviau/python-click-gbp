import click


def test_basic_chaining(runner):
    @click.group(chain=True)
    def cli():
        pass

    @cli.command('sdist')
    def sdist():
        click.echo('sdist called')

    @cli.command('bdist')
    def bdist():
        click.echo('bdist called')

    result = runner.invoke(cli, ['bdist', 'sdist', 'bdist'])
    assert not result.exception
    assert result.output.splitlines() == [
        'bdist called',
        'sdist called',
        'bdist called',
    ]


def test_chaining_help(runner):
    @click.group(chain=True)
    def cli():
        """ROOT HELP"""
        pass

    @cli.command('sdist')
    def sdist():
        """SDIST HELP"""
        click.echo('sdist called')

    @cli.command('bdist')
    def bdist():
        """BDIST HELP"""
        click.echo('bdist called')

    result = runner.invoke(cli, ['--help'])
    assert not result.exception
    assert 'COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...' in result.output
    assert 'ROOT HELP' in result.output

    result = runner.invoke(cli, ['sdist', '--help'])
    assert not result.exception
    assert 'SDIST HELP' in result.output

    result = runner.invoke(cli, ['bdist', '--help'])
    assert not result.exception
    assert 'BDIST HELP' in result.output

    result = runner.invoke(cli, ['bdist', 'sdist', '--help'])
    assert not result.exception
    assert 'SDIST HELP' in result.output


def test_chaining_with_options(runner):
    @click.group(chain=True)
    def cli():
        pass

    @cli.command('sdist')
    @click.option('--format')
    def sdist(format):
        click.echo('sdist called %s' % format)

    @cli.command('bdist')
    @click.option('--format')
    def bdist(format):
        click.echo('bdist called %s' % format)

    result = runner.invoke(cli, ['bdist', '--format=1', 'sdist', '--format=2'])
    assert not result.exception
    assert result.output.splitlines() == [
        'bdist called 1',
        'sdist called 2',
    ]


def test_chaining_with_arguments(runner):
    @click.group(chain=True)
    def cli():
        pass

    @cli.command('sdist')
    @click.argument('format')
    def sdist(format):
        click.echo('sdist called %s' % format)

    @cli.command('bdist')
    @click.argument('format')
    def bdist(format):
        click.echo('bdist called %s' % format)

    result = runner.invoke(cli, ['bdist', '1', 'sdist', '2'])
    assert not result.exception
    assert result.output.splitlines() == [
        'bdist called 1',
        'sdist called 2',
    ]


def test_context_subcommand_info_sync(recwarn):
    @click.command()
    def cli():
        pass

    def _assert_warning():
        assert 'removed in Click 3.2' in str(recwarn.pop(Warning).message)

    ctx = click.Context(cli, info_name='cli')

    assert ctx.invoked_subcommand is None

    ctx.invoked_subcommand = 'foo'
    assert ctx.invoked_subcommand == 'foo'
    assert ctx.invoked_subcommands == ['foo']

    ctx.invoked_subcommands = ['foo']
    assert ctx.invoked_subcommand == 'foo'
    assert ctx.invoked_subcommands == ['foo']

    ctx.invoked_subcommands = []
    assert ctx.invoked_subcommand is None
    assert ctx.invoked_subcommands == []

    ctx.invoked_subcommands = ['foo', 'bar']
    assert ctx.invoked_subcommand == '*'
    assert ctx.invoked_subcommands == ['*']

    assert 'removed in Click 3.2' in str(recwarn.pop(Warning).message)


def test_pipeline(runner):
    @click.group(chain=True, invoke_without_command=True)
    @click.option('-i', '--input', type=click.File('r'))
    def cli(input):
        pass

    @cli.resultcallback()
    def process_pipeline(processors, input):
        iterator = (x.rstrip('\r\n') for x in input)
        for processor in processors:
            iterator = processor(iterator)
        for item in iterator:
            click.echo(item)

    @cli.command('uppercase')
    def make_uppercase():
        def processor(iterator):
            for line in iterator:
                yield line.upper()
        return processor

    @cli.command('strip')
    def make_strip():
        def processor(iterator):
            for line in iterator:
                yield line.strip()
        return processor

    result = runner.invoke(cli, ['-i', '-'], input='foo\nbar')
    assert not result.exception
    assert result.output.splitlines() == [
        'foo',
        'bar',
    ]

    result = runner.invoke(cli, ['-i', '-', 'strip'], input='foo \n bar')
    assert not result.exception
    assert result.output.splitlines() == [
        'foo',
        'bar',
    ]

    result = runner.invoke(cli, ['-i', '-', 'strip', 'uppercase'],
                           input='foo \n bar')
    assert not result.exception
    assert result.output.splitlines() == [
        'FOO',
        'BAR',
    ]
