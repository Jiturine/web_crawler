from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

semantic_cls = pipeline(Tasks.text_classification, 'iic/nlp_structbert_sentiment-classification_chinese-base')

def classify(input_texts):
    '''对文本批量分析'''
    ids = list(input_texts.keys())
    texts = list(input_texts.values())
    batch_result = semantic_cls(input=texts)
    result_list = []
    for i in range(len(batch_result)):
        sorted_labels_scores= sorted(zip(batch_result[i]['labels'], batch_result[i]['scores']), key=lambda x: x[0] == '正面', reverse=True)
        positive_label, positive_probs = sorted_labels_scores[0]
        negative_label, negative_probs = sorted_labels_scores[1]
        is_positive = 1 if positive_probs >= negative_probs else 0
        result_list.append({"comment_id": ids[i], "is_positive": is_positive})
    return result_list

def classify_text(input_text):
    '''对单个文本进行分析'''
    result = semantic_cls(input=input_text)
    sorted_labels_scores= sorted(zip(result['labels'], result['scores']), key=lambda x: x[0] == '正面', reverse=True)
    positive_label, positive_probs = sorted_labels_scores[0]
    negative_label, negative_probs = sorted_labels_scores[1]
    is_positive = 1 if positive_probs >= negative_probs else 0
    return is_positive