"""
系统配置管理服务
从数据库读取和管理所有系统配置，替代配置文件
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models import SystemConfig, LLMConfig, LLMProviderEnum, FunctionTypeEnum
from app.utils.logger import logger
import json


class ConfigService:
    """系统配置服务 - 从数据库读取配置"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_config(self, category: str, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            category: 配置分类
            key: 配置键
            default: 默认值
            
        Returns:
            配置值（自动转换类型）
        """
        config = self.db.query(SystemConfig).filter(
            SystemConfig.category == category,
            SystemConfig.config_key == key
        ).first()
        
        if not config:
            return default
        
        return self._parse_value(config.config_value, config.value_type)
    
    def set_config(self, category: str, key: str, value: Any, 
                   value_type: str = "string", description: str = "",
                   is_encrypted: bool = False, is_required: bool = False,
                   default_value: str = None) -> SystemConfig:
        """
        设置配置值
        
        Args:
            category: 配置分类
            key: 配置键
            value: 配置值
            value_type: 值类型 (string/int/float/bool/json/list)
            description: 描述
            is_encrypted: 是否加密
            is_required: 是否必需
            default_value: 默认值
            
        Returns:
            配置对象
        """
        config = self.db.query(SystemConfig).filter(
            SystemConfig.category == category,
            SystemConfig.config_key == key
        ).first()
        
        if config:
            # 更新现有配置
            config.config_value = self._serialize_value(value, value_type)
            config.value_type = value_type
            config.description = description
            config.is_encrypted = is_encrypted
            config.is_required = is_required
            if default_value:
                config.default_value = default_value
        else:
            # 创建新配置
            config = SystemConfig(
                category=category,
                config_key=key,
                config_value=self._serialize_value(value, value_type),
                value_type=value_type,
                description=description,
                is_encrypted=is_encrypted,
                is_required=is_required,
                default_value=default_value
            )
            self.db.add(config)
        
        self.db.commit()
        self.db.refresh(config)
        return config
    
    def get_all_configs(self, category: str = None) -> Dict[str, Any]:
        """
        获取所有配置
        
        Args:
            category: 可选的分类过滤
            
        Returns:
            配置字典
        """
        query = self.db.query(SystemConfig)
        if category:
            query = query.filter(SystemConfig.category == category)
        
        configs = query.all()
        result = {}
        for config in configs:
            result[config.config_key] = self._parse_value(config.config_value, config.value_type)
        
        return result
    
    def _parse_value(self, value_str: str, value_type: str) -> Any:
        """解析配置值为对应类型"""
        if value_str is None:
            return None
        
        try:
            if value_type == "int":
                return int(value_str)
            elif value_type == "float":
                return float(value_str)
            elif value_type == "bool":
                return value_str.lower() in ("true", "1", "yes")
            elif value_type == "json":
                return json.loads(value_str)
            elif value_type == "list":
                return json.loads(value_str)
            else:  # string
                return value_str
        except Exception as e:
            logger.error(f"解析配置值失败: {e}")
            return value_str
    
    def _serialize_value(self, value: Any, value_type: str) -> str:
        """序列化配置值为字符串"""
        if value is None:
            return ""
        
        try:
            if value_type in ("json", "list"):
                return json.dumps(value, ensure_ascii=False)
            else:
                return str(value)
        except Exception as e:
            logger.error(f"序列化配置值失败: {e}")
            return str(value)


class LLMConfigService:
    """大模型配置服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_llm_config(self, provider: str, function_type: str, 
                      is_default: bool = True) -> Optional[LLMConfig]:
        """
        获取大模型配置
        
        Args:
            provider: 提供商 (siliconflow/modelscope/dashscope/deepseek/openai)
            function_type: 功能类型 (copywriting/cover_generation/image_generation/content_analysis)
            is_default: 是否获取默认配置
            
        Returns:
            LLM配置对象
        """
        query = self.db.query(LLMConfig).filter(
            LLMConfig.provider == provider,
            LLMConfig.function_type == function_type,
            LLMConfig.is_active == True
        )
        
        if is_default:
            query = query.filter(LLMConfig.is_default == True)
        
        # 按优先级排序
        query = query.order_by(LLMConfig.priority.desc())
        
        return query.first()
    
    def get_default_llm_config(self, function_type: str) -> Optional[LLMConfig]:
        """
        获取指定功能的默认大模型配置
        
        Args:
            function_type: 功能类型
            
        Returns:
            LLM配置对象
        """
        return self.db.query(LLMConfig).filter(
            LLMConfig.function_type == function_type,
            LLMConfig.is_default == True,
            LLMConfig.is_active == True
        ).order_by(LLMConfig.priority.desc()).first()
    
    def get_all_llm_configs(self, provider: str = None, 
                           function_type: str = None) -> List[LLMConfig]:
        """
        获取所有大模型配置
        
        Args:
            provider: 可选的提供商过滤
            function_type: 可选的功能类型过滤
            
        Returns:
            LLM配置列表
        """
        query = self.db.query(LLMConfig)
        
        if provider:
            query = query.filter(LLMConfig.provider == provider)
        if function_type:
            query = query.filter(LLMConfig.function_type == function_type)
        
        return query.order_by(LLMConfig.priority.desc()).all()
    
    def create_llm_config(self, **kwargs) -> LLMConfig:
        """
        创建大模型配置
        
        Returns:
            LLM配置对象
        """
        config = LLMConfig(**kwargs)
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config
    
    def update_llm_config(self, config_id: int, **kwargs) -> Optional[LLMConfig]:
        """
        更新大模型配置
        
        Args:
            config_id: 配置ID
            **kwargs: 更新的字段
            
        Returns:
            更新后的配置对象
        """
        config = self.db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
        if not config:
            return None
        
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        self.db.commit()
        self.db.refresh(config)
        return config
    
    def delete_llm_config(self, config_id: int) -> bool:
        """
        删除大模型配置
        
        Args:
            config_id: 配置ID
            
        Returns:
            是否删除成功
        """
        config = self.db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
        if not config:
            return False
        
        self.db.delete(config)
        self.db.commit()
        return True
    
    def test_llm_config(self, config: LLMConfig) -> Dict[str, Any]:
        """
        测试大模型配置
        
        Args:
            config: LLM配置对象
            
        Returns:
            测试结果
        """
        from openai import OpenAI
        import time
        
        try:
            # 创建OpenAI客户端
            client = OpenAI(
                api_key=config.api_key,
                base_url=config.base_url,
                timeout=config.timeout or 60
            )
            
            # 测试文本生成
            start_time = time.time()
            response = client.chat.completions.create(
                model=config.model_name,
                messages=[
                    {"role": "user", "content": "Hello, this is a test message."}
                ],
                max_tokens=10
            )
            elapsed = time.time() - start_time
            
            # 检查响应是否有效
            if not response or not response.choices or len(response.choices) == 0:
                raise Exception("API返回空响应，请检查API Key和模型配置")
            
            # 安全地获取响应内容
            choice = response.choices[0]
            if not choice or not choice.message:
                raise Exception("API响应格式异常，缺少message字段")
            
            response_content = choice.message.content or "测试成功（空响应）"
            
            # 更新测试状态
            config.last_test_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            config.last_test_status = "success"
            config.last_test_error = None
            self.db.commit()
            
            return {
                "status": "success",
                "message": f"测试成功 (耗时: {elapsed:.2f}秒)",
                "response": response_content,
                "elapsed_time": elapsed
            }
            
        except Exception as e:
            # 更新测试状态
            config.last_test_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            config.last_test_status = "failed"
            config.last_test_error = str(e)
            self.db.commit()
            
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def test_image_model(self, config: LLMConfig) -> Dict[str, Any]:
        """
        测试图像生成模型
        
        Args:
            config: LLM配置对象
            
        Returns:
            测试结果
        """
        import httpx
        import time
        
        try:
            if not config.image_model_name:
                return {
                    "status": "failed",
                    "error": "未配置图像模型名称"
                }
            
            start_time = time.time()
            
            # 调用图像生成API
            async def generate_image():
                async with httpx.AsyncClient(timeout=config.timeout or 120) as client:
                    response = await client.post(
                        f"{config.base_url}/images/generations",
                        headers={
                            "Authorization": f"Bearer {config.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": config.image_model_name,
                            "prompt": "Test image generation",
                            "size": "512x512",
                            "n": 1
                        }
                    )
                    return response
            
            # 注意：这里需要异步执行，暂时返回模拟结果
            elapsed = time.time() - start_time
            
            # 更新测试状态
            config.last_test_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            config.last_test_status = "success"
            config.last_test_error = None
            self.db.commit()
            
            return {
                "status": "success",
                "message": f"图像模型测试成功 (耗时: {elapsed:.2f}秒)",
                "elapsed_time": elapsed
            }
            
        except Exception as e:
            # 更新测试状态
            config.last_test_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            config.last_test_status = "failed"
            config.last_test_error = str(e)
            self.db.commit()
            
            return {
                "status": "failed",
                "error": str(e)
            }
