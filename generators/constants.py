"""Character-class constants used for phonetic pattern matching.

``vowels`` and ``consonants`` cover the Latin alphabet plus common
diacritical forms needed for European language corpora.  They are
referenced by the ``C`` and ``V`` placeholders in phonetic patterns
(see :mod:`generators.helpers`).
"""

vowels = 'AEIOUYaeiouyÄËÏÖÜäëïöüÁÉÍÓÚáéíóúÀÈÌÒÙàèìòùÂÊÎÔÛâêîôûÃÕãõÅÆØåæø'
consonants = 'BCDFGHJKLMNPQRSTVWXZbcdfghjklmnpqrstvwxzÇÑçñ'
