from app.nlp.parsers import RuleParser
from app.nlp.ast.builder import WorkflowASTBuilder
from app.nlp.ast.validator import ASTValidator
from app.nlp.complier.workflow_complier import WorkflowComplier


class WorkflowCompilerService:
    def compile_dsl(self, dsl_text: str) -> dict:
        nodes = RuleParser().parse(dsl_text)
        ast = WorkflowASTBuilder().build(nodes)
        ASTValidator().validate(ast)
        return WorkflowComplier().compile(ast)
