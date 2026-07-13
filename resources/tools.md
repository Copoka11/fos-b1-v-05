# Инструменты

## Минимальное окружение

- Python 3.10 или новее;
- NumPy и SciPy — численные операции;
- scikit-learn — pipeline, preprocessing, модели, CV и метрики;
- Matplotlib/Seaborn — визуализация;
- PyTorch и torchvision — MLP, CNN и наборы изображений;
- SHAP — дополнительная интерпретация моделей.

## Требования к воспроизводимости

1. Зафиксировать зависимости в `requirements.txt`, `pyproject.toml` или `environment.yml`.
2. Зафиксировать seed Python, NumPy и ML-фреймворка.
3. Отделить конфигурацию эксперимента от кода.
4. Сохранять метрики и параметры запуска в машиночитаемом формате.
5. Привести одну команду полного воспроизведения результата.

## Справочные страницы

- scikit-learn Pipeline: <https://scikit-learn.org/stable/modules/compose.html#pipeline>;
- model selection: <https://scikit-learn.org/stable/model_selection.html>;
- metrics: <https://scikit-learn.org/stable/modules/model_evaluation.html>;
- воспроизводимость PyTorch: <https://pytorch.org/docs/stable/notes/randomness.html>;
- SHAP: <https://shap.readthedocs.io/en/latest/>.
