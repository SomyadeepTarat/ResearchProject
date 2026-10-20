"""Interactive presentation for the reviewed-record scope experiment."""
from dataclasses import asdict, replace
import json
import streamlit as st
from claimaudit.evaluation.scope_benchmark import examples, pooled_support
from claimaudit.verification.scope import audit, recommend_resolution


def render_scope_demo():
    st.header('Do the facts belong to the same experiment?')
    st.caption('ScopeGuard · experimental ClaimAudit extension · reviewed structured inputs')
    st.warning('Synthetic demonstration. Context labels and alternatives are supplied explicitly; automatic PDF extraction and patent novelty are not established.')
    cases = list(examples(1))
    labels = {
        'joint_support':'One experiment satisfies both conditions',
        'cross_experiment_splice':'Correct numbers, different experiments',
        'partial_evidence':'A measurement is missing',
        'header_ambiguity':'A header changes the conclusion',
        'exclusive_splice':'Mutually exclusive interpretations are spliced',
        'invariant_support':'Uncertainty cannot change support',
    }
    family = st.selectbox('Scenario', list(labels), format_func=labels.get)
    record, problem = next((r,p) for r,p in cases if r['family']==family)
    st.subheader('Claim')
    st.write('There exists one listed configuration of Model A with accuracy at least 90% and latency at most 2 ms.')
    st.caption('The conjunction shares one configuration. Distinct-experiment comparisons require another claim representation and are outside this prototype.')
    st.write('Declared contexts: X and Y. ' + ('The supplied list is declared exhaustive.' if problem.closed_domain else 'The supplied evidence is not declared exhaustive.'))
    def show_facts(facts):
        if facts: st.dataframe([asdict(f) for f in facts], hide_index=True, width='stretch')
        else: st.caption('No additional measurements.')
    st.subheader('Evidence and admissible interpretations')
    show_facts(problem.facts)
    for c in problem.choices:
        st.markdown(f'**{c.locator}** — exactly one of these alternatives applies:')
        for i, alternative in enumerate(c.alternatives):
            st.write(f'Alternative {i+1}')
            show_facts(alternative)
    result = audit(problem)
    a,b,c = st.columns(3)
    a.metric('Independent number matching', 'Supported' if pooled_support(problem,False) else 'Not supported')
    b.metric('Context join, alternatives flattened', 'Supported' if pooled_support(problem,True) else 'Not supported')
    c.metric('ScopeGuard', result['status'].capitalize())
    meanings = {'supported':'Every admissible interpretation contains a joint supporting experiment.',
        'contradicted':'Every listed experiment has an observed failing condition in every interpretation, and the context domain is declared exhaustive.',
        'insufficient':'The evidence does not settle support; absence is not a contradiction.',
        'ambiguous':'Admissible source interpretations lead to different decisions.'}
    st.info(meanings[result['status']])
    suggestion = recommend_resolution(problem)
    if suggestion:
        st.subheader('Clarify the source that changes the verdict')
        st.write(f"Inspect {suggestion['source_locator']}. Whichever interpretation is correct, this single clarification settles the decision.")
        st.caption('This simulates a human reading the source. No source has been retrieved automatically.')
        index = st.selectbox('Reviewed interpretation', range(len(suggestion['conditional_statuses'])), format_func=lambda i:f'Alternative {i+1}', key=f'resolve_{family}')
        choice_index = suggestion['choice_index']
        choice = problem.choices[choice_index]
        resolved = replace(problem, facts=problem.facts+choice.alternatives[index], choices=problem.choices[:choice_index]+problem.choices[choice_index+1:])
        st.success('After reviewed clarification: '+audit(resolved)['status'])
    with st.expander('Replay record and structured input'):
        st.json({'input':asdict(problem), 'result':result, 'resolution_request':suggestion})
    st.download_button('Download audit record', json.dumps({'input':asdict(problem),'result':result},indent=2), file_name='scope_audit.json', mime='application/json')
    st.caption('Counts describe enumerated alternatives, not probabilities. The SHA-256 binds this replay record to its input; it does not authenticate the source.')
