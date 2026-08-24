"""
Model Interface
===============

定义量化交易系统中模型的基础接口。
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseModel(ABC):
    """
    模型基础接口。

    所有具体模型都应继承 BaseModel。
    """

    @abstractmethod
    def fit(self, X: Any, y: Any = None) -> None:
        """
        训练模型。

        Parameters
        ----------
        X : Any
            特征数据。
        y : Any, optional
            标签数据。
        """
        raise NotImplementedError

    @abstractmethod
    def predict(self, X: Any) -> Any:
        """
        使用模型进行预测。

        Parameters
        ----------
        X : Any
            输入特征。

        Returns
        -------
        Any
            模型预测结果。
        """
        raise NotImplementedError

    def save(self, path: str) -> None:
        """
        保存模型。

        默认未实现，具体模型可以覆盖。
        """
        raise NotImplementedError

    def load(self, path: str) -> None:
        """
        加载模型。

        默认未实现，具体模型可以覆盖。
        """
        raise NotImplementedError