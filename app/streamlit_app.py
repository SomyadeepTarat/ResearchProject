"""ClaimAudit local research demo: live claims and recorded evaluation results."""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from claimaudit.config import ExperimentConfig
from claimaudit.demo import DemoEngine, METHOD_LABELS, calibration_thresholds, filter_records, load_run
from claimaudit.evaluation.dataset import load_dataset

ROOT = Path(__file__).resolve().parents[1]
st.set_page_config(page_title='ClaimAudit', page_icon='🔎', layout='wide')


@st.cache_resource(show_spinner=False)
def get_engine(config: ExperimentConfig, offline: bool):
    return DemoEngine.load(config, offline)


def render_predictions(predictions):
    with st.container(horizontal=True):
        for name in ('embedding', 'nli', 'structure-aware'):
            prediction = predictions[name]
            with st.container(border=True, width=320):
                st.subheader(METHOD_LABELS[name])
                st.metric('Verdict', 'Supported' if prediction['verdict']=='supported' else 'Not supported')
                label = 'Cosine similarity' if name=='embedding' else 'NLI entailment'
                st.caption(f"{label}: {prediction['score']:.4f}")
                st.write(prediction['explanation'])
    st.caption('Cosine similarity is not a probability of support. NLI probabilities are uncalibrated; the hybrid retains the NLI score even when a structural check changes the verdict.')
    with st.expander('NLI class probabilities'):
        st.dataframe(pd.DataFrame([{'Class':name, 'Probability':value}
                                  for name,value in predictions['nli']['class_scores'].items()]), hide_index=True, width='stretch')
    st.subheader('Structural checks')
    for check in predictions['structure-aware']['checks']:
        with st.container(border=True):
            st.markdown(f"**{check['name'].capitalize()} · {check['status']}**")
            st.write(check['explanation'])
            for span in check['evidence_spans']:
                st.text(span)
    st.caption('Abstain means the check could not establish a conclusion. It does not mean the claim is supported.')


def verify_page(config, run, run_name):
    st.header('Verify a claim')
    st.write('Compare one claim against its evidence. The two models run locally; structural checks explain explicit numerical or comparison conflicts.')
    examples = {row.id: row for row in load_dataset(ROOT/'data/smoke.jsonl')}
    choices = ['Custom text', *examples]
    if 'evidence' not in st.session_state:
        st.session_state.evidence = examples['accuracy-2'].evidence
        st.session_state.claim = examples['accuracy-2'].claim
    def change_example():
        selected = st.session_state.example
        st.session_state.evidence = '' if selected=='Custom text' else examples[selected].evidence
        st.session_state.claim = '' if selected=='Custom text' else examples[selected].claim
        st.session_state.pop('live_result', None)
    st.selectbox('Load a synthetic smoke example', choices, index=choices.index('accuracy-2'),
                 key='example', on_change=change_example)
    left, right = st.columns(2)
    evidence = left.text_area('Source evidence', key='evidence', height=170, max_chars=20000)
    claim = right.text_area('Claim to verify', key='claim', height=170, max_chars=20000)
    defaults = (config.embedding.threshold, config.nli.threshold)
    calibrated = None
    if run:
        try:
            calibrated = calibration_thresholds(run, config)
        except (KeyError, ValueError) as exc:
            st.warning(f'Saved thresholds cannot be used: {exc}')
    use_saved = st.checkbox('Use development-selected thresholds', value=calibrated is not None,
                            disabled=calibrated is None, key='use_saved')
    using_calibration = bool(use_saved and calibrated is not None)
    if using_calibration:
        thresholds = calibrated
        st.caption(f'Calibration: {run_name} · embedding ≥ {thresholds[0]:.6f} · NLI entailment ≥ {thresholds[1]:.6f}. No thresholds are fitted to your input.')
    else:
        with st.expander('Exploratory thresholds', expanded=True):
            a,b=st.columns(2)
            thresholds=(a.number_input('Embedding threshold', min_value=-1., max_value=1., value=defaults[0], step=.01, format='%.6f'),
                        b.number_input('NLI threshold', min_value=0., max_value=1., value=defaults[1], step=.01, format='%.6f'))
            st.caption('Manual thresholds affect this live prediction only; saved evaluation results stay fixed.')
    with st.expander('Verification settings'):
        numeric = st.checkbox('Numerical checks', value=True)
        comparison = st.checkbox('Comparison-direction checks', value=True)
        offline = st.checkbox('Use cached models only', value=True,
                              help='Uncheck to allow downloading the pinned public model weights when needed.')
        st.caption('Text that exceeds either model’s token limit is rejected rather than truncated. The structural parser supports a limited explicit grammar.')
    fingerprint = (evidence, claim, *thresholds, numeric, comparison, offline, using_calibration, run_name)
    if st.button('Run verification', type='primary'):
        st.session_state.pop('live_result', None)
        if not evidence.strip() or not claim.strip():
            st.error('Enter both source evidence and a claim.')
        else:
            try:
                with st.spinner('Running the local verification models…'):
                    result = get_engine(config, offline).verify(evidence, claim, *thresholds, numeric=numeric, comparison=comparison)
                result['threshold_source'] = f'development:{run_name}' if using_calibration else 'manual_exploration'
                st.session_state.live_result = (fingerprint, result)
            except (OSError, ValueError, RuntimeError, ImportError, TypeError) as exc:
                st.error(f'Verification could not run: {exc}')
                st.caption('For missing weights, uncheck “Use cached models only”. Install the models extra if model libraries are missing.')
    saved = st.session_state.get('live_result')
    if saved:
        if saved[0] != fingerprint:
            st.info('Inputs or settings changed. Run verification again to see a current result.')
        else:
            render_predictions(saved[1]['predictions'])
            st.download_button('Download this prediction', json.dumps(saved[1], indent=2, default=str),
                               file_name='claimaudit_prediction.json', mime='application/json')


def evaluation_page(run):
    st.header('Explore the evaluation')
    if run is None:
        st.info('No completed evaluation is available. Create one with the benchmark command in the README.')
        return
    summary = run['summary']
    count = summary['splits']['test']['examples']
    group_count = len(summary['splits']['test']['groups'])
    st.warning(f'Controlled synthetic study: {count} test examples, {group_count} template families. Author-defined labels are not independently reviewed. These results do not establish real-paper performance.')
    table=[]
    for name, metric in summary['test_metrics'].items():
        interval = summary['bootstrap']['macro_f1_intervals'][name]
        table.append({'Method':METHOD_LABELS[name], 'Macro-F1':metric['macro_f1'],
                      '95% interval':f'[{interval[0]:.3f}, {interval[1]:.3f}]',
                      'Support precision':metric['support_precision'], 'Support recall':metric['support_recall'],
                      'Supported false rejection':metric['supported_false_rejection_rate']})
    st.dataframe(pd.DataFrame(table), hide_index=True, width='stretch')
    diagnostic=summary['structural_diagnostics']['structure-aware']
    a,b,c=st.columns(3)
    a.metric('Corrected NLI mistakes',diagnostic['corrected_nli_errors'])
    b.metric('Introduced mistakes',diagnostic['introduced_errors'])
    c.metric('Check coverage',f"{diagnostic['any_conclusive_check_rate']:.0%}")
    st.caption('The intervals resample whole families. With so few independent families, they are exploratory. Saved results reflect the recorded code and settings; live verification uses the current checkout.')
    st.download_button('Download the evaluation report', run['report'], file_name='claimaudit_evaluation.md', mime='text/markdown')
    st.subheader('Inspect saved predictions')
    a,b,c=st.columns(3)
    split=a.selectbox('Split',['test','dev'])
    method=b.selectbox('Method for filtering',list(METHOD_LABELS),format_func=METHOD_LABELS.get)
    label=c.selectbox('Gold label',['All','supported','numeric_contradiction','comparison_contradiction','unsupported'])
    groups=sorted({r['group_id'] for r in run['records'] if r['split']==split})
    group=st.selectbox('Template family',['All',*groups])
    errors_only=st.checkbox('Show only mistakes for the selected method',value=True)
    records=filter_records(run['records'],split=split,method=method,errors_only=errors_only,
                           label=None if label=='All' else label,group=None if group=='All' else group)
    st.caption(f'{len(records)} matching examples. Gold labels guide this display only; verifiers do not receive them.')
    if not records:
        st.info('No examples match these filters.')
        return
    selected=st.selectbox('Saved example',[r['id'] for r in records])
    row=next(r for r in records if r['id']==selected)
    st.write(f"Gold label: **{row['label']}**")
    a,b=st.columns(2)
    with a:
        st.markdown('**Evidence**')
        st.text(row['evidence'])
    with b:
        st.markdown('**Claim**')
        st.text(row['claim'])
    st.caption(f"Annotation rationale: {row['rationale']}")
    render_predictions(row['methods'])
    with st.expander('All method and ablation outputs'):
        st.json(row['methods'])
    st.download_button('Download selected saved example',json.dumps(row,indent=2),file_name='claimaudit_saved_example.json',mime='application/json')


def main():
    st.title('ClaimAudit')
    st.caption('Evidence-grounded claim verification · research prototype')
    config=ExperimentConfig.load(ROOT/'experiments/controlled.toml')
    page=st.sidebar.radio('Workspace',['Verify a claim','Explore evaluation','About'])
    directories=sorted(path.parent for path in (ROOT/'results').glob('*/complete.json'))
    run, run_name=None,None
    if directories:
        run_name=st.sidebar.selectbox('Saved evaluation',[p.name for p in directories])
        directory=next(p for p in directories if p.name==run_name)
        try:
            run=load_run(directory)
            st.sidebar.caption('Saved artifact hashes verified.')
        except (OSError,ValueError,KeyError,TypeError) as exc:
            st.sidebar.error(f'Cannot display this run: {exc}')
    else:
        st.sidebar.caption('No saved evaluation found. Live verification uses exploratory thresholds.')
    st.sidebar.caption('Live inputs stay in this session and are not written to dataset or result files.')
    if page=='Verify a claim':
        verify_page(config,run,run_name)
    elif page=='Explore evaluation':
        evaluation_page(run)
    else:
        st.header('About this prototype')
        st.write('ClaimAudit compares embedding similarity, NLI, and NLI with explicit numerical and comparison checks. It tests a hypothesis about verification; it does not assume the hybrid is better.')
        st.write('The current controlled study uses 300 synthetic examples. Thresholds were chosen on 60 development examples before evaluating 60 test examples; 180 examples were reserved and unused. Independent paper-derived annotation remains outstanding.')
        st.write('A structural check can veto NLI support but cannot promote a rejected claim. Unknown grammar, scope, units, or conflicting evidence cause abstention. Negation, ranges, and contextual claims can fall outside the structural parser.')
        st.caption('See README.md, docs/structure_checks.md, and docs/evaluation.md in the repository for the full protocol and limitations.')


main()
