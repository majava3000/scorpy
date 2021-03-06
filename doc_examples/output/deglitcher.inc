.. Generated by gen_deglitcher.py

.. literalinclude:: ../doc_examples/gen_deglitcher.py
   :language: python
   :dedent: 4
   :linenos:
   :start-after: example-start-here
   :end-before: example-end-here

.. wavedrom::

    {signal: [
      { name: 'input', wave: 'z===.=.=..=..=...=..=...z', data: ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']},
      {},
      { name: 'result1', wave: 'z=...=.=..=..=...=..=...z', data: ['C', 'D', 'E', 'F', 'G', 'H', 'I']},
      { name: 'result2', wave: 'z=........=..=...=..=...z', data: ['E', 'F', 'G', 'H', 'I']},
      { name: 'result3', wave: 'z=...............=......z', data: ['G', 'I']},
      { name: 'result4', wave: 'z=......................z', data: ['I']},
      ],
      head: { tick: -1 },
      config: { skin: 'narrow' },
    }
