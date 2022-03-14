import pytest

import merlin.models.tf as ml
from merlin.models.data.synthetic import SyntheticData


@pytest.mark.parametrize("run_eagerly", [True, False])
def test_model_encode(ecommerce_data: SyntheticData, run_eagerly):
    prediction_task = ml.PredictionTasks(ecommerce_data.schema)

    body = ml.InputBlock(ecommerce_data.schema).connect(ml.MLPBlock([64]))
    model = body.connect(prediction_task)
    model.compile(run_eagerly=run_eagerly, optimizer="adam")

    model.fit(ecommerce_data.dataset, batch_size=50, epochs=1)

    data = model.batch_predict(ecommerce_data.dataset, batch_size=10)
    ddf = data.compute(scheduler="synchronous")

    assert len(list(ddf.columns)) == 27
    assert all([task in list(ddf.columns) for task in model.block.last.task_names])


def test_two_tower_embedding_extraction(ecommerce_data: SyntheticData):
    two_tower = ml.TwoTowerBlock(ecommerce_data.schema, query_tower=ml.MLPBlock([64, 128]))

    model = two_tower.connect(
        ml.ItemRetrievalTask(ecommerce_data.schema, target_name="click", metrics=[])
    )
    model.compile(run_eagerly=True, optimizer="adam")
    model.fit(ecommerce_data.dataset, batch_size=50, epochs=1)

    item_embs = model.item_embeddings(ecommerce_data.dataset, batch_size=10)
    item_embs_ddf = item_embs.compute(scheduler="synchronous")

    assert len(list(item_embs_ddf.columns)) == 5 + 128

    user_embs = model.query_embeddings(ecommerce_data.dataset, batch_size=10)
    user_embs_ddf = user_embs.compute(scheduler="synchronous")

    assert len(list(user_embs_ddf.columns)) == 13 + 128