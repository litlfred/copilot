import json
import jsonschema
from jsonschema import validate
import os
import logging

from gogo_git import GoGoGit

# Configure logging for this module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class StructuredProposalResponseError(Exception):
    pass

class StructuredProposalResponse:
    _schema = None

    @classmethod
    def load_schema(cls):
        if cls._schema is None:
            schema_path = os.path.join(os.path.dirname(__file__), 'structured_proposal_response.schema.json')
            logger.info(f"Loading schema from {schema_path}")
            try:
                with open(schema_path, 'r') as f:
                    cls._schema = json.load(f)
                logger.info("Schema loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load schema: {e}")
                raise StructuredProposalResponseError(f"Could not load schema: {e}")
        return cls._schema

    def __init__(self, json_str):
        logger.info("Initializing StructuredProposalResponse instance.")
        try:
            self.data = json.loads(json_str)
            logger.debug(f"Parsed JSON: {self.data}")
        except Exception as e:
            logger.error(f"Invalid JSON input: {e}")
            raise StructuredProposalResponseError(f"Invalid JSON: {e}")
        schema = self.load_schema()
        try:
            validate(instance=self.data, schema=schema)
            logger.info("JSON validated successfully against schema.")
        except jsonschema.exceptions.ValidationError as e:
            logger.error(f"JSON does not comply with StructuredProposalResponse schema: {e}")
            raise StructuredProposalResponseError(f"JSON does not comply with StructuredProposalResponse schema: {e}")

    def apply_patch(self, repo_path):
        patch_content = self.data['patch']
        patch_file = os.path.join(repo_path, '.gogo_patch.diff')
        logger.info(f"Writing patch to {patch_file}")
        try:
            with open(patch_file, 'w') as f:
                f.write(patch_content)
            logger.info("Patch file written. Applying patch to repository.")
            g = GoGoGit(repo_path)
            result = g.apply_patch(patch_file)
            logger.info("Patch applied successfully.")
        except Exception as e:
            logger.error(f"Failed to apply patch: {e}")
            raise StructuredProposalResponseError(f"Failed to apply patch: {e}")
        finally:
            if os.path.exists(patch_file):
                os.remove(patch_file)
                logger.info(f"Removed temporary patch file: {patch_file}")
        return result

    def commit(self, repo_path):
        commit_message = self.data['commit_message']
        logger.info(f"Committing changes to repo at {repo_path} with message: {commit_message}")
        try:
            g = GoGoGit(repo_path)
            g._run_git(['add', '-A'])
            result = g._run_git(['commit', '-m', commit_message])
            logger.info("Commit successful.")
        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            raise StructuredProposalResponseError(f"Failed to commit changes: {e}")
        return result

    # Getter and setter methods for all fields
    def get_patch(self):
        logger.debug("Getting patch field.")
        return self.data.get('patch')

    def set_patch(self, patch):
        logger.debug("Setting patch field.")
        self.data['patch'] = patch

    def get_explanation(self):
        logger.debug("Getting explanation field.")
        return self.data.get('explanation')

    def set_explanation(self, explanation):
        logger.debug("Setting explanation field.")
        self.data['explanation'] = explanation

    def get_errors(self):
        logger.debug("Getting errors field.")
        return self.data.get('errors')

    def set_errors(self, errors):
        logger.debug("Setting errors field.")
        self.data['errors'] = errors

    def get_install(self):
        logger.debug("Getting install field.")
        return self.data.get('install')

    def set_install(self, instr):
        logger.debug("Setting install field.")
        self.data['install'] = instr

    def get_gadget(self):
        logger.debug("Getting gadget field.")
        return self.data.get('gadget')

    def set_gadget(self, gadget):
        logger.debug("Setting gadget field.")
        self.data['gadget'] = gadget

    def get_commit_message(self):
        logger.debug("Getting commit_message field.")
        return self.data.get('commit_message')

    def set_commit_message(self, msg):
        logger.debug("Setting commit_message field.")
        self.data['commit_message'] = msg

    def get_version(self):
        logger.debug("Getting version field.")
        return self.data.get('version', 'v0.1')

    def set_version(self, version):
        logger.debug("Setting version field.")
        self.data['version'] = version

    def to_json(self):
        logger.debug("Serializing StructuredProposalResponse to JSON.")
        return json.dumps(self.data, indent=2)