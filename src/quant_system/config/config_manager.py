"""
QuantTradingSystem V3
Configuration Manager

职责：
1. 加载 01_config 下的 YAML 配置文件
2. 提供统一配置访问接口
3. 验证配置完整性
4. 验证配置参数类型和范围
5. 检查 Paper / Live 交易安全状态
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import yaml


class ConfigError(Exception):
    """配置系统异常。"""


class ConfigManager:
    """
    QuantTradingSystem V3 配置管理器。

    默认读取：

    01_config/
        ├── config.yaml
        ├── symbols.yaml
        ├── strategy.yaml
        ├── risk.yaml
        ├── broker.yaml
        └── logging.yaml
    """

    REQUIRED_FILES = (
        "config.yaml",
        "symbols.yaml",
        "strategy.yaml",
        "risk.yaml",
        "broker.yaml",
        "logging.yaml",
    )

    def __init__(
        self,
        config_dir: str | Path = "01_config",
        auto_load: bool = True,
        validate: bool = True,
    ) -> None:
        """
        初始化配置管理器。

        Parameters
        ----------
        config_dir:
            YAML 配置目录。

        auto_load:
            是否自动加载配置。

        validate:
            加载后是否自动验证。
        """

        self.config_dir = Path(config_dir).resolve()

        self._configs: Dict[str, Dict[str, Any]] = {}

        if auto_load:
            self.load_all()

            if validate:
                self.validate_all()

    # ==========================================================
    # 01. Loading
    # ==========================================================

    def load_all(self) -> None:
        """加载全部 YAML 配置文件。"""

        if not self.config_dir.exists():
            raise ConfigError(
                f"配置目录不存在: {self.config_dir}"
            )

        if not self.config_dir.is_dir():
            raise ConfigError(
                f"配置路径不是目录: {self.config_dir}"
            )

        for filename in self.REQUIRED_FILES:
            self.load_file(filename)

    def load_file(
        self,
        filename: str,
    ) -> Dict[str, Any]:
        """
        加载单个 YAML 文件。

        Parameters
        ----------
        filename:
            YAML 文件名。

        Returns
        -------
        dict
            配置内容。
        """

        path = self.config_dir / filename

        if not path.exists():
            raise ConfigError(
                f"配置文件不存在: {path}"
            )

        if not path.is_file():
            raise ConfigError(
                f"配置路径不是文件: {path}"
            )

        try:
            with path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = yaml.safe_load(file)

        except yaml.YAMLError as exc:
            raise ConfigError(
                f"YAML 格式错误: {path}\n{exc}"
            ) from exc

        except OSError as exc:
            raise ConfigError(
                f"读取配置文件失败: {path}\n{exc}"
            ) from exc

        # 空 YAML 文件
        if data is None:
            data = {}

        # 顶层必须是 dict
        if not isinstance(data, dict):
            raise ConfigError(
                f"配置文件顶层必须是字典: {path}"
            )

        # config.yaml → config
        # risk.yaml   → risk
        # broker.yaml → broker
        config_name = Path(filename).stem

        self._configs[config_name] = data

        return data

    # ==========================================================
    # 02. Reload
    # ==========================================================

    def reload(self) -> None:
        """重新加载全部配置。"""

        self._configs.clear()

        self.load_all()

        self.validate_all()

    # ==========================================================
    # 03. Basic Access
    # ==========================================================

    def get(
        self,
        config_name: str,
        key: Optional[str] = None,
        default: Any = None,
    ) -> Any:
        """
        获取配置。

        示例：

            config.get("config")

            config.get(
                "config",
                "system"
            )

            config.get(
                "config",
                "system.timezone"
            )

            config.get(
                "risk",
                "portfolio.max_positions"
            )
        """

        if config_name not in self._configs:
            raise ConfigError(
                f"配置不存在: {config_name}"
            )

        data: Any = self._configs[config_name]

        if key is None:
            return data

        for part in key.split("."):

            if not isinstance(data, dict):
                return default

            if part not in data:
                return default

            data = data[part]

        return data

    def require(
        self,
        config_name: str,
        key: Optional[str] = None,
    ) -> Any:
        """
        获取必需配置。

        如果不存在，直接抛出 ConfigError。
        """

        value = self.get(
            config_name=config_name,
            key=key,
            default=None,
        )

        if value is None:

            full_key = (
                config_name
                if key is None
                else f"{config_name}.{key}"
            )

            raise ConfigError(
                f"必需配置不存在: {full_key}"
            )

        return value

    # ==========================================================
    # 04. Specific Configuration
    # ==========================================================

    def get_system(self) -> Dict[str, Any]:
        """获取系统配置。"""

        return self.require(
            "config",
            "system",
        )

    def get_symbols(self) -> Dict[str, Any]:
        """获取交易标的配置。"""

        return self.require(
            "symbols",
            "symbols",
        )

    def get_strategy(self) -> Dict[str, Any]:
        """获取策略配置。"""

        return self.require(
            "strategy",
            "strategy",
        )

    def get_risk(self) -> Dict[str, Any]:
        """获取风控配置。"""

        return self.require(
            "risk",
            "risk",
        )

    def get_broker(self) -> Dict[str, Any]:
        """获取券商配置。"""

        return self.require(
            "broker",
            "broker",
        )

    def get_logging(self) -> Dict[str, Any]:
        """获取日志配置。"""

        return self.require(
            "logging",
            "logging",
        )

    # ==========================================================
    # 05. Environment
    # ==========================================================

    def get_environment(self) -> str:
        """获取运行环境。"""

        return self.require(
            "config",
            "system.environment",
        )

    def get_trading_mode(self) -> str:
        """获取交易模式。"""

        return self.require(
            "config",
            "system.mode",
        )

    def is_live(self) -> bool:
        """判断是否为实盘模式。"""

        environment = (
            self.get_environment()
            .lower()
        )

        mode = (
            self.get_trading_mode()
            .lower()
        )

        broker_live = self.get(
            "broker",
            "environment.live_trading",
            False,
        )

        return (
            environment == "production"
            or mode == "live"
            or bool(broker_live)
        )

    def is_paper(self) -> bool:
        """判断是否为模拟盘。"""

        mode = (
            self.get_trading_mode()
            .lower()
        )

        broker_mode = self.get(
            "broker",
            "environment.mode",
            "paper",
        )

        return (
            mode == "paper"
            or str(
                broker_mode
            ).lower() == "paper"
        )

    # ==========================================================
    # 06. Validation
    # ==========================================================

    def validate_all(self) -> None:
        """执行全部配置验证。"""

        self._validate_required_configs()

        self._validate_system()

        self._validate_symbols()

        self._validate_strategy()

        self._validate_risk()

        self._validate_broker()

        self._validate_logging()

        self._validate_live_safety()

    def _validate_required_configs(self) -> None:
        """检查六个配置文件是否全部加载。"""

        for filename in self.REQUIRED_FILES:

            config_name = Path(
                filename
            ).stem

            if config_name not in self._configs:

                raise ConfigError(
                    f"配置尚未加载: {filename}"
                )

    # ==========================================================
    # 07. System Validation
    # ==========================================================

    def _validate_system(self) -> None:
        """验证系统配置。"""

        system = self.get_system()

        required = (
            "name",
            "version",
            "environment",
            "timezone",
            "base_currency",
            "mode",
        )

        self._require_keys(
            system,
            required,
            "config.system",
        )

        environment = system[
            "environment"
        ]

        allowed_environments = {
            "development",
            "backtest",
            "paper",
            "production",
        }

        if environment not in allowed_environments:

            raise ConfigError(
                f"无效 environment: "
                f"{environment}"
            )

        mode = system["mode"]

        allowed_modes = {
            "paper",
            "live",
            "backtest",
        }

        if mode not in allowed_modes:

            raise ConfigError(
                f"无效 trading mode: "
                f"{mode}"
            )

    # ==========================================================
    # 08. Symbols Validation
    # ==========================================================

    def _validate_symbols(self) -> None:
        """验证交易标的配置。"""

        symbols = self.get_symbols()

        stocks = symbols.get(
            "stocks",
            [],
        )

        etfs = symbols.get(
            "etfs",
            [],
        )

        indices = symbols.get(
            "indices",
            [],
        )

        for group_name, items in (
            ("stocks", stocks),
            ("etfs", etfs),
            ("indices", indices),
        ):

            if not isinstance(
                items,
                list,
            ):

                raise ConfigError(
                    f"{group_name} 必须是 list"
                )

            for item in items:

                if not isinstance(
                    item,
                    dict,
                ):

                    raise ConfigError(
                        f"{group_name} "
                        f"中存在无效配置"
                    )

                if "symbol" not in item:

                    raise ConfigError(
                        f"{group_name} "
                        f"中缺少 symbol"
                    )

                if not item["symbol"]:

                    raise ConfigError(
                        f"{group_name} "
                        f"存在空 symbol"
                    )

    # ==========================================================
    # 09. Strategy Validation
    # ==========================================================

    def _validate_strategy(self) -> None:
        """验证策略配置。"""

        strategy = self.get_strategy()

        global_config = strategy.get(
            "global",
            {},
        )

        if not isinstance(
            global_config,
            dict,
        ):

            raise ConfigError(
                "strategy.global "
                "必须是 dict"
            )

        holding = global_config.get(
            "holding_period",
            {},
        )

        min_days = holding.get(
            "min_days"
        )

        max_days = holding.get(
            "max_days"
        )

        if (
            min_days is not None
            and max_days is not None
        ):

            if min_days > max_days:

                raise ConfigError(
                    "strategy.global."
                    "holding_period: "
                    "min_days 不能大于 "
                    "max_days"
                )

        alpha = strategy.get(
            "alpha_model",
            {},
        )

        factor_count = alpha.get(
            "factor_count",
            {},
        )

        min_factor = factor_count.get(
            "min"
        )

        max_factor = factor_count.get(
            "max"
        )

        if (
            min_factor is not None
            and max_factor is not None
        ):

            if min_factor > max_factor:

                raise ConfigError(
                    "strategy.alpha_model."
                    "factor_count: "
                    "min 不能大于 max"
                )

    # ==========================================================
    # 10. Risk Validation
    # ==========================================================

    def _validate_risk(self) -> None:
        """验证风控配置。"""

        risk = self.get_risk()

        position = risk.get(
            "position",
            {},
        )

        portfolio = risk.get(
            "portfolio",
            {},
        )

        sector = risk.get(
            "sector",
            {},
        )

        # ------------------------------------------------------
        # 单股票最大权重
        # ------------------------------------------------------

        max_stock_weight = position.get(
            "max_stock_weight"
        )

        if max_stock_weight is not None:

            self._validate_ratio(
                max_stock_weight,
                "risk.position."
                "max_stock_weight",
            )

        # ------------------------------------------------------
        # 行业最大权重
        # ------------------------------------------------------

        max_sector_weight = sector.get(
            "max_sector_weight"
        )

        if max_sector_weight is not None:

            self._validate_ratio(
                max_sector_weight,
                "risk.sector."
                "max_sector_weight",
            )

        # ------------------------------------------------------
        # 最大总敞口
        # ------------------------------------------------------

        max_gross = portfolio.get(
            "max_gross_exposure"
        )

        if max_gross is not None:

            if max_gross <= 0:

                raise ConfigError(
                    "risk.portfolio."
                    "max_gross_exposure "
                    "必须大于 0"
                )

        # ------------------------------------------------------
        # VaR
        # ------------------------------------------------------

        var = risk.get(
            "var",
            {},
        )

        confidence = var.get(
            "confidence_level"
        )

        if confidence is not None:

            if not 0 < confidence < 1:

                raise ConfigError(
                    "risk.var."
                    "confidence_level "
                    "必须位于 0 和 1 "
                    "之间"
                )

        # ------------------------------------------------------
        # Drawdown
        # ------------------------------------------------------

        drawdown = risk.get(
            "drawdown",
            {},
        )

        warning = drawdown.get(
            "warning"
        )

        level_4 = drawdown.get(
            "level_4"
        )

        if (
            warning is not None
            and level_4 is not None
        ):

            if warning >= level_4:

                raise ConfigError(
                    "risk.drawdown."
                    "warning 必须小于 "
                    "level_4"
                )

    # ==========================================================
    # 11. Broker Validation
    # ==========================================================

    def _validate_broker(self) -> None:
        """验证 Broker 配置。"""

        broker = self.get_broker()

        if not broker.get(
            "enabled",
            False,
        ):
            return

        connection = broker.get(
            "connection",
            {},
        )

        host = connection.get(
            "host"
        )

        port = connection.get(
            "port"
        )

        if not host:

            raise ConfigError(
                "broker.connection.host "
                "不能为空"
            )

        if not isinstance(
            port,
            int,
        ):

            raise ConfigError(
                "broker.connection.port "
                "必须是整数"
            )

        if not 1 <= port <= 65535:

            raise ConfigError(
                "broker.connection.port "
                "无效"
            )

        client_id = connection.get(
            "client_id"
        )

        if not isinstance(
            client_id,
            int,
        ):

            raise ConfigError(
                "broker.connection."
                "client_id 必须是整数"
            )

        broker_mode = broker.get(
            "environment.mode"
        )

        # 兼容标准嵌套结构
        if broker_mode is None:

            environment = broker.get(
                "environment",
                {},
            )

            broker_mode = environment.get(
                "mode"
            )

        if broker_mode not in {
            "paper",
            "live",
        }:

            raise ConfigError(
                "broker.environment.mode "
                "必须是 paper 或 live"
            )

    # ==========================================================
    # 12. Logging Validation
    # ==========================================================

    def _validate_logging(self) -> None:
        """验证日志配置。"""

        logging = self.get_logging()

        if not logging.get(
            "enabled",
            True,
        ):
            return

        level = logging.get(
            "level",
            "INFO",
        )

        allowed_levels = {
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }

        if level not in allowed_levels:

            raise ConfigError(
                f"无效日志级别: {level}"
            )

    # ==========================================================
    # 13. Live Trading Safety
    # ==========================================================

    def _validate_live_safety(self) -> None:
        """
        实盘安全检查。

        防止多个配置项组合错误，
        导致系统意外进入实盘。
        """

        if not self.is_live():
            return

        broker_live_enabled = self.get(
            "broker",
            "live.enabled",
            False,
        )

        live_trading = self.get(
            "config",
            "system.live_trading",
            False,
        )

        require_confirmation = self.get(
            "broker",
            "live.require_confirmation",
            True,
        )

        if not broker_live_enabled:

            raise ConfigError(
                "检测到实盘模式，但 "
                "broker.live.enabled=false"
            )

        if not live_trading:

            raise ConfigError(
                "检测到实盘模式，但 "
                "config.system.live_trading=false"
            )

        if not require_confirmation:

            raise ConfigError(
                "实盘模式必须要求二次确认"
            )

    # ==========================================================
    # 14. Helpers
    # ==========================================================

    @staticmethod
    def _require_keys(
        data: Dict[str, Any],
        keys: Iterable[str],
        path: str,
    ) -> None:
        """检查必需字段。"""

        for key in keys:

            if key not in data:

                raise ConfigError(
                    f"缺少必需配置: "
                    f"{path}.{key}"
                )

    @staticmethod
    def _validate_ratio(
        value: Any,
        name: str,
    ) -> None:
        """验证比例参数。"""

        if not isinstance(
            value,
            (int, float),
        ):

            raise ConfigError(
                f"{name} 必须是数字"
            )

        if not 0 <= value <= 1:

            raise ConfigError(
                f"{name} 必须位于 "
                f"0 和 1 之间"
            )

    # ==========================================================
    # 15. Utility
    # ==========================================================

    def list_configs(self) -> list[str]:
        """返回已经加载的配置名称。"""

        return list(
            self._configs.keys()
        )

    def has(
        self,
        config_name: str,
    ) -> bool:
        """检查配置是否存在。"""

        return config_name in self._configs

    def get_all(
        self,
    ) -> Dict[str, Dict[str, Any]]:
        """
        返回全部配置。

        注意：
        不建议直接修改返回值。
        """

        return self._configs.copy()

    def __repr__(self) -> str:
        return (
            "ConfigManager("
            f"config_dir={self.config_dir!s}, "
            f"configs={self.list_configs()}"
            ")"
        )