from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

def classify(input_text):
    semantic_cls = pipeline(Tasks.text_classification, 'iic/nlp_structbert_sentiment-classification_chinese-base')
    result = semantic_cls(input=input_text)
    sorted_labels_scores= sorted(zip(result['labels'], result['scores']), key=lambda x: x[0] == '正面', reverse=True)
    positive_label, positive_probs = sorted_labels_scores[0]
    negative_label, negative_probs = sorted_labels_scores[1]
    is_positive = 1 if positive_probs >= negative_probs else 0
    return {"positive_label": positive_label, "negative_label": negative_label, "is_positive": is_positive}
