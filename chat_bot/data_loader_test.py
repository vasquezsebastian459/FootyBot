import requests
import time

import nlpaug.augmenter.char as nac

# Lower the probability of character swaps (e.g. 5% of characters)
aug = nac.KeyboardAug(aug_char_p=0.1, aug_word_p=0.1)

text = "How many goals did Mbappe score in La Liga this season?"
augmented = aug.augment(text)

print(augmented)



if __name__ == "__main__":

    question = "How many goals did Messi score in La Liga this season?"
    question = "How many goals did Messi score in La Liga this season?"
    question = "How mny goals did mbappe score in la liga this season?"

    league = "la liga this"

    start_run = time.time()

    print(f"QUESTION: {question}")

    # TEST AGGREGATION
    start_time = time.time()
    res = requests.post("http://localhost:5005/predict_aggregation", json={"question": question})
    end_time = time.time()
    print(f"Time taken to aggregation: {end_time - start_time} seconds")
    print(res.json())

    # TEST ENTITY OF INTEREST
    start_time = time.time()
    res = requests.post("http://localhost:5005/predict_entity_of_interest", json={"question": question})
    end_time = time.time()
    print(f"Time taken to entity of interest: {end_time - start_time} seconds")
    print(res.json())
    
    # TEST ENTITY RECOGNITION
    start_time = time.time()
    res = requests.post("http://localhost:5005/entity_recognition", json={"question": question})
    end_time = time.time()
    print(f"Time taken to entity recognition: {end_time - start_time} seconds")
    print(res.json())


    # TEST LEAGUE MATCHING
    start_time = time.time()
    res = requests.post("http://localhost:5005/match_league", json={"query": league, "threshold": 0.5})
    end_time = time.time()
    print(f"Time taken to match league: {end_time - start_time} seconds")
    print(res.json())

    end_run = time.time()
    print(f"Total time taken: {end_run - start_run} seconds")