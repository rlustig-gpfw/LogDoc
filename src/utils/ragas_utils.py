import time
from langchain_openai import ChatOpenAI
from typing import Dict, Iterable, List
import pandas as pd
from langchain_core.runnables import Runnable
from ragas.dataset_schema import EvaluationResult
from ragas.testset import Testset
from ragas import evaluate, EvaluationDataset
from ragas.metrics import (
    ContextRecall,
    ContextPrecision,
    Faithfulness,
    ResponseRelevancy,
    NoiseSensitivity,
)
from src.utils.config import get_config


def run_ragas_evaluation(retriever_chain: Runnable, chain_name: str, dataset: Testset):
    """
    Run Ragas evaluation for a given retriever chain and return the results.
    """
    config = get_config()
    evaluator_llm = config.get_evaluator_model()

    metrics = [
        ContextRecall(),
        ContextPrecision(),
        Faithfulness(),
        ResponseRelevancy(),
        NoiseSensitivity(),
    ]

    rows = []
    for row in dataset:
        question = row.eval_sample.user_input

        t_start = time.perf_counter()
        out = retriever_chain.invoke({"question" : question})
        latency_ms = (time.perf_counter() - t_start) * 1000

        resp = out["response"]
        response_text = resp.content if hasattr(resp, "content") else resp.get("content", "")
        # retrieved_contexts = [out["context"]]
        retrieved_contexts = [c.page_content for c in out["context"]]

        # Token usage (assuming OpenAI metadata)
        usage = getattr(resp, "response_metadata", {}).get("token_usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

        rows.append({
            "user_input" : question,
            "retrieved_contexts" : retrieved_contexts,
            "response" : response_text,
            "reference_contexts" : row.eval_sample.reference_contexts,
            "reference" : row.eval_sample.reference,

            # Latency
            "latency_ms": latency_ms,

            # Token usage
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        })
        time.sleep(5)  # Sleep to avoid rate limiting

    eval_df = pd.DataFrame(rows)
    evaluation_dataset = EvaluationDataset.from_pandas(eval_df)
    result = evaluate(
        dataset=evaluation_dataset,
        metrics=metrics,
        llm=evaluator_llm,
    )

    return {
        "chain_name" : chain_name,
        "results" : result,
        "eval_df" : eval_df,
        "summary": {
            "avg_latency_ms": float(eval_df["latency_ms"].mean()),
            "p95_latency_ms": float(eval_df["latency_ms"].quantile(0.95)),
            "avg_total_tokens": float(eval_df["total_tokens"].mean()),
            "total_tokens_sum": int(eval_df["total_tokens"].sum()),
        }
    }


def _filter_result_metrics(result: EvaluationResult, keep_metrics: Iterable):
    df = result.to_pandas()

    # Coerce numeric columns
    df_num = df.apply(pd.to_numeric, errors="coerce")

    out = {}
    for metric in keep_metrics:
        if metric in df_num.columns:
            out[metric] = float(df_num[metric].mean())
    return out


def compare_ragas_results(all_evaluation_results: List[Dict[str, EvaluationResult]]):
    """ 
    Compare RAGAS results for different retriever chains and return a table.
    """
    keep_metrics = [
        "context_recall",
        "context_precision",
        "faithfulness",
        "answer_relevancy",
        "noise_sensitivity(mode=relevant)",
    ]
    
    rows = {}
    for evaluation_result in all_evaluation_results:
        chain_name = evaluation_result["chain_name"]
        eval_result = evaluation_result["results"]
        metrics = _filter_result_metrics(eval_result, keep_metrics)
        rows[chain_name] = metrics

    df = pd.DataFrame.from_dict(rows, orient="index")
    
    return df.round(3)