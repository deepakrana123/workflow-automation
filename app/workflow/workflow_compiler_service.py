class WorkflowCompilerService:

    def __init__(
        self,
        dsl_generator,
        rule_parser,
        ast_builder,
        ast_validator,
        workflow_compiler
    ):
        self.dsl_generator = dsl_generator
        self.rule_parser = rule_parser
        self.ast_builder = ast_builder
        self.ast_validator = ast_validator
        self.workflow_compiler = workflow_compiler

    def compile(
        self,
        workflow_type: str,
        workflow_json: dict,
    ):

        dsl = self.dsl_generator.generate(
            workflow_type,
            workflow_json
        )

        nodes = self.rule_parser.parse(dsl)

        ast = self.ast_builder.build(nodes)

        self.ast_validator.validate(ast)

        compiled = self.workflow_compiler.compile(ast)

        return {
            "dsl": dsl,
            "ast": ast,
            "compiled": compiled,
        }