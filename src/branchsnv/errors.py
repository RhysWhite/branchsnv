"""BRANCHSNV exception types."""


class BranchSNVError(Exception):
    """Base class for expected user-facing errors."""


class NexusFormatError(BranchSNVError):
    """Raised when a NEXUS alignment is malformed or unsupported."""


class NewickFormatError(BranchSNVError):
    """Raised when a Newick tree is malformed or unsupported."""


class ValidationError(BranchSNVError):
    """Raised when inputs are individually valid but incompatible."""


class SelectionError(BranchSNVError):
    """Raised when a requested branch cannot be selected unambiguously."""
