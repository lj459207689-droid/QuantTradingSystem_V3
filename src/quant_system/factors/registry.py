"""
Factor registry.

负责注册、查找和创建因子。
"""

from __future__ import annotations

from typing import Type

from .base import BaseFactor


class FactorRegistry:
    """
    因子注册表。

    职责：
    - 注册 Factor
    - 按名称查找 Factor
    - 创建 Factor
    - 列出全部 Factor
    - 按类别组织 Factor
    """

    def __init__(self) -> None:
        self._factors: dict[str, Type[BaseFactor]] = {}

    def register(
        self,
        factor_class: Type[BaseFactor],
    ) -> None:
        """
        注册一个因子类。
        """

        if not isinstance(factor_class, type):
            raise TypeError(
                "factor_class must be a class"
            )

        if not issubclass(factor_class, BaseFactor):
            raise TypeError(
                "factor_class must inherit from BaseFactor"
            )

        # name 是 property，因此这里通过 class 的
        # name 属性无法直接得到实例值。
        #
        # 约定具体 Factor 必须提供 class_name。
        name = getattr(
            factor_class,
            "factor_name",
            None,
        )

        if not name:
            raise ValueError(
                f"{factor_class.__name__} "
                "must define 'factor_name'"
            )

        if name in self._factors:
            raise ValueError(
                f"Factor already registered: {name}"
            )

        self._factors[name] = factor_class

    def unregister(
        self,
        name: str,
    ) -> None:
        """
        删除已经注册的因子。
        """

        if name not in self._factors:
            raise KeyError(
                f"Factor not registered: {name}"
            )

        del self._factors[name]

    def get(
        self,
        name: str,
    ) -> Type[BaseFactor]:
        """
        根据名称获取因子类。
        """

        if name not in self._factors:
            raise KeyError(
                f"Factor not found: {name}"
            )

        return self._factors[name]

    def create(
        self,
        name: str,
        **kwargs,
    ) -> BaseFactor:
        """
        根据名称创建因子实例。
        """

        factor_class = self.get(name)

        return factor_class(**kwargs)

    def exists(
        self,
        name: str,
    ) -> bool:
        """
        判断因子是否已经注册。
        """

        return name in self._factors

    def names(self) -> list[str]:
        """
        返回所有因子名称。
        """

        return sorted(self._factors.keys())

    def categories(self) -> dict[str, list[str]]:
        """
        按类别返回因子名称。
        """

        result: dict[str, list[str]] = {}

        for factor_class in self._factors.values():

            category = getattr(
                factor_class,
                "category",
                "unknown",
            )

            name = getattr(
                factor_class,
                "factor_name",
                factor_class.__name__,
            )

            result.setdefault(
                category,
                [],
            ).append(name)

        for names in result.values():
            names.sort()

        return result

    def clear(self) -> None:
        """
        清空注册表。
        """

        self._factors.clear()

    def __len__(self) -> int:
        return len(self._factors)

    def __contains__(
        self,
        name: str,
    ) -> bool:
        return self.exists(name)

    def __repr__(self) -> str:
        return (
            f"FactorRegistry("
            f"count={len(self)}, "
            f"factors={self.names()}"
            f")"
        )
