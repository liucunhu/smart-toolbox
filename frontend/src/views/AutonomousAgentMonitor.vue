<template>
  <div class="autonomous-agent-monitor">
    <el-row :gutter="20">
      <!-- 系统状态概览 -->
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🤖 自主智能体监控系统</span>
              <el-tag type="success" size="small">运行中</el-tag>
            </div>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="6">
              <el-statistic title="工作流总数" :value="stats.workflows.total">
                <template #suffix>个</template>
              </el-statistic>
            </el-col>
            <el-col :span="6">
              <el-statistic title="活跃实例" :value="stats.workflows.active_instances">
                <template #suffix>个</template>
              </el-statistic>
            </el-col>
            <el-col :span="6">
              <el-statistic title="经验记录" :value="stats.experiences.total">
                <template #suffix>条</template>
              </el-statistic>
            </el-col>
            <el-col :span="6">
              <el-statistic title="智能体数量" :value="stats.agents.total">
                <template #suffix>个</template>
              </el-statistic>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 任务规划面板 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📋 任务规划</span>
            </div>
          </template>
          
          <el-form :model="planningForm" label-width="100px">
            <el-form-item label="目标描述">
              <el-input 
                v-model="planningForm.description" 
                type="textarea"
                :rows="3"
                placeholder="输入任务目标，如：创作一篇关于AI的文章并发布到头条"
              />
            </el-form-item>
            
            <el-form-item label="优先级">
              <el-slider v-model="planningForm.priority" :min="1" :max="10" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="handleDecomposeGoal" :loading="decomposing">
                分解目标
              </el-button>
            </el-form-item>
          </el-form>
          
          <!-- 分解结果 -->
          <div v-if="decomposedTasks.length > 0" style="margin-top: 20px;">
            <el-divider content-position="left">任务分解结果</el-divider>
            
            <!-- 批量执行按钮 -->
            <el-button 
              type="success" 
              size="small" 
              @click="executeAllTasks"
              :loading="executingAll"
              :disabled="decomposedTasks.length === 0"
              style="margin-bottom: 15px;"
            >
              🚀 执行所有任务
            </el-button>
            
            <el-timeline>
              <el-timeline-item 
                v-for="(task, index) in decomposedTasks" 
                :key="task.task_id"
                :timestamp="`步骤 ${index + 1}`"
                placement="top"
              >
                <el-card>
                  <h4>{{ task.description }}</h4>
                  <p>智能体类型: {{ task.agent_type }}</p>
                  <p>优先级: {{ task.priority }}</p>
                  
                  <!-- 任务状态和执行按钮 -->
                  <div style="margin-top: 10px; display: flex; align-items: center; gap: 10px;">
                    <el-tag size="small" :type="getTaskStatusType(task)">
                      {{ getTaskStatusText(task) }}
                    </el-tag>
                    
                    <el-button 
                      v-if="!task.executing && !task.completed" 
                      size="small" 
                      type="primary"
                      @click="executeSingleTask(task)"
                      :loading="task.executing"
                    >
                      执行
                    </el-button>
                    
                    <el-button 
                      v-if="task.completed" 
                      size="small" 
                      @click="showTaskResult(task)"
                    >
                      查看结果
                    </el-button>
                  </div>
                  
                  <!-- 执行结果显示 -->
                  <div v-if="task.result" style="margin-top: 10px; padding: 10px; background: #f5f7fa; border-radius: 4px;">
                    <strong>执行结果:</strong>
                    <pre style="margin-top: 5px; font-size: 12px;">{{ JSON.stringify(task.result, null, 2) }}</pre>
                  </div>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-card>
      </el-col>

      <!-- 强化学习控制面板 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🧠 强化学习控制</span>
            </div>
          </template>
          
          <el-descriptions :column="1" border>
            <el-descriptions-item label="探索率">
              {{ rlStats.exploration_rate?.toFixed(4) || 'N/A' }}
            </el-descriptions-item>
            <el-descriptions-item label="Q表大小">
              {{ rlStats.q_table_size || 0 }}
            </el-descriptions-item>
          </el-descriptions>
          
          <el-divider />
          
          <el-form :model="rlForm" label-width="100px">
            <el-form-item label="状态">
              <el-input v-model="rlForm.state" placeholder="输入状态" />
            </el-form-item>
            
            <el-form-item label="可用动作">
              <el-input 
                v-model="rlForm.actionsText" 
                placeholder="用逗号分隔，如：action1,action2,action3"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="handleChooseAction" :loading="choosingAction">
                选择动作
              </el-button>
              <el-button @click="handleDecayExploration">衰减探索率</el-button>
            </el-form-item>
          </el-form>
          
          <!-- 动作选择结果 -->
          <div v-if="actionResult" style="margin-top: 20px;">
            <el-alert 
              :title="`选择的动作: ${actionResult.chosen_action}`" 
              type="success" 
              :closable="false"
            />
            <div style="margin-top: 10px;">
              <strong>Q值分布:</strong>
              <pre>{{ JSON.stringify(actionResult.q_values, null, 2) }}</pre>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 知识迁移面板 -->
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🌐 跨平台知识迁移</span>
            </div>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form :model="knowledgeForm" label-width="120px">
                <el-form-item label="源平台">
                  <el-select v-model="knowledgeForm.sourcePlatform" placeholder="选择平台">
                    <el-option label="今日头条" value="toutiao" />
                    <el-option label="抖音" value="douyin" />
                    <el-option label="快手" value="kuaishou" />
                    <el-option label="小红书" value="xiaohongshu" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="目标平台">
                  <el-select v-model="knowledgeForm.targetPlatform" placeholder="选择平台">
                    <el-option label="今日头条" value="toutiao" />
                    <el-option label="抖音" value="douyin" />
                    <el-option label="快手" value="kuaishou" />
                    <el-option label="小红书" value="xiaohongshu" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="知识类型">
                  <el-select v-model="knowledgeForm.knowledgeType" placeholder="选择类型">
                    <el-option label="最佳实践" value="best_practices" />
                    <el-option label="模式规则" value="patterns" />
                  </el-select>
                </el-form-item>
                
                <el-form-item>
                  <el-button type="primary" @click="handleTransferKnowledge" :loading="transferring">
                    迁移知识
                  </el-button>
                </el-form-item>
              </el-form>
            </el-col>
            
            <el-col :span="16">
              <!-- 迁移统计 -->
              <el-descriptions title="迁移统计" :column="2" border>
                <el-descriptions-item label="总迁移次数">
                  {{ transferStats.total_transfers || 0 }}
                </el-descriptions-item>
                <el-descriptions-item label="知识库大小">
                  {{ transferStats.knowledge_base_size || 0 }}
                </el-descriptions-item>
              </el-descriptions>
              
              <!-- 迁移历史 -->
              <div v-if="transferHistory.length > 0" style="margin-top: 20px;">
                <el-divider content-position="left">最近迁移记录</el-divider>
                <el-table :data="transferHistory" style="width: 100%">
                  <el-table-column prop="source" label="源平台" width="120" />
                  <el-table-column prop="target" label="目标平台" width="120" />
                  <el-table-column prop="timestamp" label="时间" />
                </el-table>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 智能体列表 -->
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🤖 智能体列表</span>
              <div>
                <el-button type="primary" size="small" @click="showRegisterDialog = true">注册智能体</el-button>
                <el-button size="small" @click="fetchAgentsList">刷新</el-button>
              </div>
            </div>
          </template>
          
          <el-table :data="agentsList" style="width: 100%" v-loading="loadingAgents">
            <el-table-column prop="agent_type" label="智能体类型" width="180">
              <template #default="{ row }">
                <el-tag :type="getAgentTypeColor(row.agent_type)">{{ row.agent_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="row.status === 'idle' ? 'success' : 'warning'">
                  {{ row.status === 'idle' ? '空闲' : '忙碌' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="capabilities" label="能力" min-width="200">
              <template #default="{ row }">
                <el-tag 
                  v-for="cap in row.capabilities" 
                  :key="cap" 
                  size="small" 
                  style="margin-right: 5px;"
                >
                  {{ cap }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="completed_tasks" label="完成任务" width="120" />
            <el-table-column prop="failed_tasks" label="失败任务" width="120" />
            <el-table-column prop="load" label="负载" width="120">
              <template #default="{ row }">
                <el-progress :percentage="Math.round(row.load * 100)" :stroke-width="8" />
              </template>
            </el-table-column>
            <el-table-column prop="last_heartbeat" label="最后心跳" width="180">
              <template #default="{ row }">
                {{ formatTime(row.last_heartbeat) }}
              </template>
            </el-table-column>
          </el-table>
          
          <el-empty v-if="!loadingAgents && agentsList.length === 0" description="暂无智能体，请点击右上角'注册智能体'按钮添加" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 任务执行历史 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📊 任务执行历史</span>
              <el-button size="small" @click="fetchExecutionHistory">刷新</el-button>
            </div>
          </template>
          
          <el-table :data="executionHistory" style="width: 100%" v-loading="loadingHistory">
            <el-table-column prop="task_id" label="任务ID" width="200" show-overflow-tooltip />
            <el-table-column prop="agent_type" label="智能体类型" width="150">
              <template #default="{ row }">
                <el-tag size="small" :type="getAgentTypeColor(row.agent_type)">{{ row.agent_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
                  {{ row.status === 'success' ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="duration" label="耗时(秒)" width="100">
              <template #default="{ row }">
                {{ row.duration?.toFixed(2) || 'N/A' }}
              </template>
            </el-table-column>
            <el-table-column prop="start_time" label="开始时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.start_time) }}
              </template>
            </el-table-column>
          </el-table>
          
          <el-empty v-if="!loadingHistory && executionHistory.length === 0" description="暂无执行记录" />
        </el-card>
      </el-col>
      
      <!-- 执行统计 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📈 执行统计</span>
              <el-button size="small" @click="fetchExecutionStats">刷新</el-button>
            </div>
          </template>
          
          <div v-for="(stat, type) in executionStats" :key="type" style="margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
              <el-tag size="small" :type="getAgentTypeColor(type)">{{ type }}</el-tag>
              <span style="font-size: 12px; color: #999;">成功率: {{ (stat.success_rate * 100).toFixed(1) }}%</span>
            </div>
            <el-progress 
              :percentage="Math.round(stat.success_rate * 100)" 
              :color="getProgressColor(stat.success_rate)"
              :stroke-width="10"
            />
            <div style="font-size: 12px; color: #666; margin-top: 3px;">
              总任务: {{ stat.total_tasks }} | 成功: {{ stat.success_count }} | 失败: {{ stat.failed_count }}
            </div>
          </div>
          
          <el-empty v-if="Object.keys(executionStats).length === 0" description="暂无统计数据" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 注册智能体对话框 -->
    <el-dialog v-model="showRegisterDialog" title="注册智能体" width="500px">
      <el-form :model="registerForm" label-width="100px">
        <el-form-item label="智能体类型" required>
          <el-select v-model="registerForm.agent_type" placeholder="选择智能体类型" style="width: 100%">
            <el-option label="研究智能体 (research)" value="research" />
            <el-option label="规划智能体 (planning)" value="planning" />
            <el-option label="内容生成智能体 (content_generation)" value="content_generation" />
            <el-option label="合规检查智能体 (compliance_check)" value="compliance_check" />
            <el-option label="图片生成智能体 (image_generation)" value="image_generation" />
            <el-option label="分发智能体 (distribution)" value="distribution" />
            <el-option label="养号智能体 (nurturing)" value="nurturing" />
            <el-option label="通用智能体 (general)" value="general" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="能力标签">
          <el-input 
            v-model="registerForm.capabilitiesText" 
            placeholder="用逗号分隔，如：article_writing,copywriting"
          />
          <div style="color: #999; font-size: 12px; margin-top: 5px;">
            提示：多个能力用逗号分隔，留空则使用默认能力
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showRegisterDialog = false">取消</el-button>
        <el-button type="primary" @click="handleRegisterAgent" :loading="registering">注册</el-button>
      </template>
    </el-dialog>

    <!-- Phase 5: 工作流管理面板 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🔄 工作流管理 (Phase 5)</span>
              <div>
                <el-button type="primary" size="small" @click="showWorkflowDialog = true">创建工作流</el-button>
                <el-button size="small" @click="fetchWorkflows">刷新</el-button>
              </div>
            </div>
          </template>
          
          <el-table :data="workflows" style="width: 100%" v-loading="loadingWorkflows">
            <el-table-column prop="name" label="工作流名称" width="200" />
            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="getWorkflowStatusType(row.status)">
                  {{ getWorkflowStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="progress" label="进度" width="150">
              <template #default="{ row }">
                <el-progress :percentage="Math.round(row.progress * 100)" :stroke-width="8" />
              </template>
            </el-table-column>
            <el-table-column prop="total_tasks" label="任务数" width="100" />
            <el-table-column prop="completed_tasks" label="已完成" width="100" />
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button size="small" @click="viewWorkflowStatus(row)">查看详情</el-button>
                <el-button v-if="row.status === 'pending'" size="small" type="success" @click="executeWorkflow(row)">执行</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <el-empty v-if="!loadingWorkflows && workflows.length === 0" description="暂无工作流，点击右上角'创建工作流'按钮添加" />
        </el-card>
      </el-col>
    </el-row>

    <!-- Phase 6: 学习洞察面板 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🧠 学习洞察 (Phase 6)</span>
              <el-select v-model="selectedAgentType" size="small" style="width: 150px" @change="fetchLearningInsights">
                <el-option label="研究智能体" value="research" />
                <el-option label="内容生成" value="content_generation" />
                <el-option label="合规检查" value="compliance_check" />
                <el-option label="图片生成" value="image_generation" />
                <el-option label="分发智能体" value="distribution" />
                <el-option label="规划智能体" value="planning" />
                <el-option label="养号智能体" value="nurturing" />
              </el-select>
            </div>
          </template>
          
          <el-descriptions :column="1" border>
            <el-descriptions-item label="经验数量">
              {{ learningInsights.experience_count || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="总体成功率">
              {{ (learningInsights.overall_success_rate * 100 || 0).toFixed(1) }}%
            </el-descriptions-item>
          </el-descriptions>
          
          <div v-if="learningInsights.recent_trends" style="margin-top: 15px;">
            <el-divider content-position="left">近期趋势</el-divider>
            <p><strong>趋势:</strong> {{ getTrendText(learningInsights.recent_trends.trend) }}</p>
            <p>最近成功率: {{ (learningInsights.recent_trends.recent_success_rate * 100).toFixed(1) }}%</p>
            <p>之前成功率: {{ (learningInsights.recent_trends.previous_success_rate * 100).toFixed(1) }}%</p>
            <el-progress 
              :percentage="learningInsights.recent_trends.recent_success_rate * 100" 
              :color="getProgressColor(learningInsights.recent_trends.recent_success_rate)"
            />
          </div>
          
          <div v-if="learningInsights.optimization_suggestions && learningInsights.optimization_suggestions.length > 0" style="margin-top: 15px;">
            <el-divider content-position="left">优化建议</el-divider>
            <el-alert 
              v-for="(suggestion, index) in learningInsights.optimization_suggestions"
              :key="index"
              :title="suggestion.message"
              :type="getAlertType(suggestion.priority)"
              :closable="false"
              style="margin-bottom: 10px;"
            />
          </div>
        </el-card>
      </el-col>
      
      <!-- Phase 6: A/B测试面板 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🧪 A/B测试 (Phase 6)</span>
              <el-button type="primary" size="small" @click="showABTestDialog = true">创建测试</el-button>
            </div>
          </template>
          
          <el-table :data="abTests" style="width: 100%" v-loading="loadingABTests">
            <el-table-column prop="name" label="测试名称" width="150" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'running' ? 'success' : 'info'">
                  {{ row.status === 'running' ? '运行中' : '已停止' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="total_samples" label="样本数" width="100" />
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button size="small" @click="analyzeABTest(row.test_id)">分析</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <el-empty v-if="!loadingABTests && abTests.length === 0" description="暂无A/B测试" />
        </el-card>
      </el-col>
    </el-row>

    <!-- Phase 6: 性能分析面板 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📈 性能分析 (Phase 6)</span>
              <el-select v-model="selectedAgentTypeForPerformance" size="small" style="width: 150px" @change="fetchPerformanceAnalysis">
                <el-option label="研究智能体" value="research" />
                <el-option label="内容生成" value="content_generation" />
                <el-option label="合规检查" value="compliance_check" />
                <el-option label="图片生成" value="image_generation" />
                <el-option label="分发智能体" value="distribution" />
                <el-option label="规划智能体" value="planning" />
                <el-option label="养号智能体" value="nurturing" />
              </el-select>
            </div>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="8">
              <el-statistic title="平均耗时" :value="performanceData.duration?.avg || 0" suffix="秒" />
            </el-col>
            <el-col :span="8">
              <el-statistic title="成功率" :value="(performanceData.success_rate?.avg || 0) * 100" suffix="%" />
            </el-col>
            <el-col :span="8">
              <el-statistic title="样本数量" :value="performanceData.duration?.samples || 0" suffix="个" />
            </el-col>
          </el-row>
          
          <div v-if="optimizationSuggestions.length > 0" style="margin-top: 20px;">
            <el-divider content-position="left">优化建议</el-divider>
            <el-alert 
              v-for="(suggestion, index) in optimizationSuggestions"
              :key="index"
              :title="suggestion.message"
              :type="getAlertType(suggestion.priority)"
              :closable="false"
              style="margin-bottom: 10px;"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Phase 5: 创建工作流对话框 -->
    <el-dialog v-model="showWorkflowDialog" title="创建工作流" width="600px">
      <el-form :model="workflowForm" label-width="100px">
        <el-form-item label="工作流名称" required>
          <el-input v-model="workflowForm.name" placeholder="例如：内容创作全流程" />
        </el-form-item>
        
        <el-form-item label="目标描述" required>
          <el-input 
            v-model="workflowForm.description" 
            type="textarea"
            :rows="3"
            placeholder="输入任务目标，系统将自动分解并创建工作流"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showWorkflowDialog = false">取消</el-button>
        <el-button type="primary" @click="createAndExecuteWorkflow" :loading="creatingWorkflow">
          创建并执行
        </el-button>
      </template>
    </el-dialog>

    <!-- Phase 5: 工作流状态对话框 -->
    <el-dialog v-model="showWorkflowStatusDialog" title="工作流状态" width="700px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="工作流名称">
          {{ currentWorkflow?.name }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getWorkflowStatusType(currentWorkflow?.status)">
            {{ getWorkflowStatusText(currentWorkflow?.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="进度">
          <el-progress :percentage="Math.round(currentWorkflow?.progress * 100 || 0)" />
        </el-descriptions-item>
        <el-descriptions-item label="任务完成情况">
          {{ currentWorkflow?.completed_tasks }} / {{ currentWorkflow?.total_tasks }}
        </el-descriptions-item>
      </el-descriptions>
      
      <div v-if="currentWorkflow?.tasks && currentWorkflow.tasks.length > 0" style="margin-top: 20px;">
        <el-divider content-position="left">任务详情</el-divider>
        <el-table :data="currentWorkflow.tasks" style="width: 100%">
          <el-table-column prop="task_id" label="任务ID" width="150" />
          <el-table-column prop="agent_type" label="智能体类型" width="150" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="duration" label="耗时(秒)" width="100">
            <template #default="{ row }">
              {{ row.duration?.toFixed(2) || 'N/A' }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- Phase 6: 创建A/B测试对话框 -->
    <el-dialog v-model="showABTestDialog" title="创建A/B测试" width="500px">
      <el-form :model="abTestForm" label-width="100px">
        <el-form-item label="测试名称" required>
          <el-input v-model="abTestForm.test_name" placeholder="例如：标题风格测试" />
        </el-form-item>
        
        <el-form-item label="变体列表" required>
          <el-input 
            v-model="abTestForm.variantsText" 
            placeholder="用逗号分隔，如：professional,casual,technical"
          />
          <div style="color: #999; font-size: 12px; margin-top: 5px;">
            提示：至少需要2个变体
          </div>
        </el-form-item>
        
        <el-form-item label="评估指标">
          <el-select v-model="abTestForm.metric" style="width: 100%">
            <el-option label="成功率" value="success_rate" />
            <el-option label="平均耗时" value="duration" />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showABTestDialog = false">取消</el-button>
        <el-button type="primary" @click="createABTest" :loading="creatingABTest">创建</el-button>
      </template>
    </el-dialog>

    <!-- Phase 6: A/B测试结果对话框 -->
    <el-dialog v-model="showABTestResultDialog" title="A/B测试结果分析" width="600px">
      <div v-if="abTestAnalysis">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="测试名称">
            {{ abTestAnalysis.name }}
          </el-descriptions-item>
          <el-descriptions-item label="总样本数">
            {{ abTestAnalysis.total_samples }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div style="margin-top: 20px;">
          <el-divider content-position="left">变体分析</el-divider>
          <el-table :data="Object.entries(abTestAnalysis.variant_analysis || {}).map(([k, v]) => ({ variant: k, ...v }))" style="width: 100%">
            <el-table-column prop="variant" label="变体" width="150" />
            <el-table-column prop="count" label="样本数" width="100" />
            <el-table-column prop="success_rate" label="成功率" width="120">
              <template #default="{ row }">
                {{ (row.success_rate * 100).toFixed(1) }}%
              </template>
            </el-table-column>
            <el-table-column prop="avg_metric" label="平均指标">
              <template #default="{ row }">
                {{ row.avg_metric.toFixed(3) }}
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <el-alert 
          v-if="abTestAnalysis.best_variant"
          :title="`推荐使用变体: ${abTestAnalysis.best_variant}`"
          type="success"
          :closable="false"
          style="margin-top: 15px;"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import apiClient from '../utils/api'

// 系统统计
const stats = reactive({
  workflows: { total: 0, active_instances: 0 },
  experiences: { total: 0 },
  agents: { total: 0, idle: 0, busy: 0 }
})

// 任务规划
const planningForm = reactive({
  description: '',
  priority: 5
})
const decomposing = ref(false)
const decomposedTasks = ref<any[]>([])

// 强化学习
const rlStats = reactive({
  exploration_rate: 0.1,
  q_table_size: 0
})
const rlForm = reactive({
  state: '',
  actionsText: ''
})
const choosingAction = ref(false)
const actionResult = ref<any>(null)

// 知识迁移
const knowledgeForm = reactive({
  sourcePlatform: '',
  targetPlatform: '',
  knowledgeType: 'best_practices'
})
const transferring = ref(false)
const transferStats = reactive({
  total_transfers: 0,
  knowledge_base_size: 0
})
const transferHistory = ref<any[]>([])

// 智能体列表
const agentsList = ref<any[]>([])
const loadingAgents = ref(false)

// 注册智能体
const showRegisterDialog = ref(false)
const registering = ref(false)
const registerForm = reactive({
  agent_type: '',
  capabilitiesText: ''
})

// 任务执行
const executingAll = ref(false)
const executionHistory = ref<any[]>([])
const loadingHistory = ref(false)
const executionStats = ref<Record<string, any>>({})

// Phase 5: 工作流管理
const workflows = ref<any[]>([])
const loadingWorkflows = ref(false)
const showWorkflowDialog = ref(false)
const creatingWorkflow = ref(false)
const workflowForm = reactive({
  name: '',
  description: ''
})
const showWorkflowStatusDialog = ref(false)
const currentWorkflow = ref<any>(null)

// Phase 6: 学习洞察
const selectedAgentType = ref('research')
const learningInsights = ref<any>({})

// Phase 6: A/B测试
const abTests = ref<any[]>([])
const loadingABTests = ref(false)
const showABTestDialog = ref(false)
const creatingABTest = ref(false)
const abTestForm = reactive({
  test_name: '',
  variantsText: '',
  metric: 'success_rate'
})
const showABTestResultDialog = ref(false)
const abTestAnalysis = ref<any>(null)

// Phase 6: 性能分析
const selectedAgentTypeForPerformance = ref('research')
const performanceData = ref<any>({})
const optimizationSuggestions = ref<any[]>([])

// 获取系统状态
const fetchSystemStatus = async () => {
  try {
    const response = await apiClient.get('/agents/system/status')
    if (response.data.status === 'success') {
      Object.assign(stats, response.data)
    }
  } catch (error) {
    console.error('获取系统状态失败:', error)
  }
}

// 获取RL统计
const fetchRLStats = async () => {
  try {
    const response = await apiClient.get('/agents/autonomous/learning/q-table')
    if (response.data.status === 'success') {
      rlStats.q_table_size = response.data.q_table_size
    }
  } catch (error) {
    console.error('获取RL统计失败:', error)
  }
}

// 获取迁移统计
const fetchTransferStats = async () => {
  try {
    const response = await apiClient.get('/agents/autonomous/knowledge/statistics')
    if (response.data.status === 'success') {
      Object.assign(transferStats, response.data.statistics)
    }
  } catch (error) {
    console.error('获取迁移统计失败:', error)
  }
}

// 获取智能体列表
const fetchAgentsList = async () => {
  loadingAgents.value = true
  try {
    const response = await apiClient.get('/agents/list')
    if (response.data.status === 'success') {
      agentsList.value = response.data.agents
    }
  } catch (error) {
    console.error('获取智能体列表失败:', error)
    ElMessage.error('获取智能体列表失败')
  } finally {
    loadingAgents.value = false
  }
}

// 获取智能体类型颜色
const getAgentTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    'research': 'purple',
    'planning': 'blue',
    'content_generation': 'green',
    'compliance_check': 'orange',
    'image_generation': 'pink',
    'distribution': 'cyan',
    'nurturing': 'brown',
    'general': 'gray'
  }
  return colorMap[type] || ''
}

// 格式化时间
const formatTime = (timeStr: string | null) => {
  if (!timeStr) return '从未'
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  return date.toLocaleDateString('zh-CN')
}

// 格式化日期时间
const formatDateTime = (timeStr: string | null) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取任务状态类型
const getTaskStatusType = (task: any) => {
  if (task.executing) return 'warning'
  if (task.completed) return 'success'
  if (task.error) return 'danger'
  return 'info'
}

// 获取任务状态文本
const getTaskStatusText = (task: any) => {
  if (task.executing) return '执行中...'
  if (task.completed) return '已完成'
  if (task.error) return '失败'
  return '待执行'
}

// 获取进度条颜色
const getProgressColor = (rate: number) => {
  if (rate >= 0.9) return '#67c23a'
  if (rate >= 0.7) return '#e6a23c'
  return '#f56c6c'
}

// Phase 5: 获取工作流状态类型
const getWorkflowStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    'pending': 'info',
    'running': 'warning',
    'completed': 'success',
    'failed': 'danger',
    'paused': 'info'
  }
  return typeMap[status] || 'info'
}

// Phase 5: 获取工作流状态文本
const getWorkflowStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    'pending': '待执行',
    'running': '运行中',
    'completed': '已完成',
    'failed': '失败',
    'paused': '已暂停'
  }
  return textMap[status] || status
}

// Phase 6: 获取趋势文本
const getTrendText = (trend: string) => {
  const textMap: Record<string, string> = {
    'improving': '📈 上升',
    'declining': '📉 下降',
    'stable': '➡️ 稳定'
  }
  return textMap[trend] || trend
}

// Phase 6: 获取警告类型
const getAlertType = (priority: string) => {
  const typeMap: Record<string, string> = {
    'high': 'error',
    'medium': 'warning',
    'low': 'info'
  }
  return typeMap[priority] || 'info'
}

// 注册智能体
const handleRegisterAgent = async () => {
  if (!registerForm.agent_type) {
    ElMessage.warning('请选择智能体类型')
    return
  }
  
  registering.value = true
  try {
    // 解析能力标签
    const capabilities = registerForm.capabilitiesText
      ? registerForm.capabilitiesText.split(',').map(s => s.trim()).filter(s => s)
      : []
    
    const response = await apiClient.post('/agents/register', {
      agent_type: registerForm.agent_type,
      capabilities: capabilities
    })
    
    if (response.data.status === 'success') {
      ElMessage.success('智能体注册成功')
      showRegisterDialog.value = false
      // 重置表单
      registerForm.agent_type = ''
      registerForm.capabilitiesText = ''
      // 刷新列表
      fetchAgentsList()
      fetchSystemStatus()
    }
  } catch (error: any) {
    ElMessage.error('注册失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    registering.value = false
  }
}

// 执行单个任务
const executeSingleTask = async (task: any) => {
  task.executing = true
  task.error = null
  
  try {
    const response = await apiClient.post('/agents/autonomous/execute', {
      agent_type: task.agent_type,
      task_params: {
        task_type: task.description.split(' - ')[1] || 'default',
        description: task.description
      },
      task_id: task.task_id
    })
    
    if (response.data.status === 'success') {
      task.completed = true
      task.result = response.data.data
      ElMessage.success(`任务执行成功: ${task.description}`)
    } else {
      task.error = response.data.error
      ElMessage.error('任务执行失败')
    }
  } catch (error: any) {
    task.error = error.message
    ElMessage.error('任务执行失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    task.executing = false
  }
}

// 执行所有任务
const executeAllTasks = async () => {
  if (decomposedTasks.value.length === 0) {
    ElMessage.warning('没有可执行的任务')
    return
  }
  
  executingAll.value = true
  
  try {
    for (const task of decomposedTasks.value) {
      if (!task.completed) {
        await executeSingleTask(task)
        // 每个任务之间稍作延迟，避免请求过快
        await new Promise(resolve => setTimeout(resolve, 500))
      }
    }
    
    ElMessage.success('所有任务执行完成')
    // 刷新执行历史
    fetchExecutionHistory()
    fetchExecutionStats()
  } catch (error: any) {
    ElMessage.error('批量执行失败: ' + error.message)
  } finally {
    executingAll.value = false
  }
}

// 显示任务结果
const showTaskResult = (task: any) => {
  if (task.result) {
    ElMessage({
      message: `任务结果已显示在卡片中`,
      type: 'info',
      duration: 2000
    })
  }
}

// 获取执行历史
const fetchExecutionHistory = async () => {
  loadingHistory.value = true
  try {
    const response = await apiClient.get('/agents/autonomous/execution/history', {
      params: { limit: 20 }
    })
    
    if (response.data.status === 'success') {
      executionHistory.value = response.data.history
    }
  } catch (error: any) {
    console.error('获取执行历史失败:', error)
  } finally {
    loadingHistory.value = false
  }
}

// 获取执行统计
const fetchExecutionStats = async () => {
  try {
    const response = await apiClient.get('/agents/autonomous/execution/stats')
    
    if (response.data.status === 'success') {
      executionStats.value = response.data.stats
    }
  } catch (error: any) {
    console.error('获取执行统计失败:', error)
  }
}

// 分解目标
const handleDecomposeGoal = async () => {
  if (!planningForm.description) {
    ElMessage.warning('请输入目标描述')
    return
  }
  
  decomposing.value = true
  try {
    const response = await apiClient.post('/agents/autonomous/planning/decompose', {
      description: planningForm.description,
      priority: planningForm.priority
    })
    
    if (response.data.status === 'success') {
      decomposedTasks.value = response.data.tasks
      ElMessage.success('目标分解成功')
    }
  } catch (error: any) {
    ElMessage.error('目标分解失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    decomposing.value = false
  }
}

// 选择动作
const handleChooseAction = async () => {
  if (!rlForm.state || !rlForm.actionsText) {
    ElMessage.warning('请填写状态和可用动作')
    return
  }
  
  const availableActions = rlForm.actionsText.split(',').map(s => s.trim()).filter(s => s)
  
  choosingAction.value = true
  try {
    const response = await apiClient.post('/agents/autonomous/learning/choose-action', {
      state: rlForm.state,
      available_actions: availableActions
    })
    
    if (response.data.status === 'success') {
      actionResult.value = response.data
      ElMessage.success(`已选择动作: ${response.data.chosen_action}`)
    }
  } catch (error: any) {
    ElMessage.error('动作选择失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    choosingAction.value = false
  }
}

// 衰减探索率
const handleDecayExploration = async () => {
  try {
    const response = await apiClient.post('/agents/autonomous/learning/decay-exploration')
    if (response.data.status === 'success') {
      ElMessage.success(`探索率已从 ${response.data.old_exploration_rate.toFixed(4)} 衰减到 ${response.data.new_exploration_rate.toFixed(4)}`)
      fetchRLStats()
    }
  } catch (error: any) {
    ElMessage.error('衰减失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 迁移知识
const handleTransferKnowledge = async () => {
  if (!knowledgeForm.sourcePlatform || !knowledgeForm.targetPlatform) {
    ElMessage.warning('请选择源平台和目标平台')
    return
  }
  
  transferring.value = true
  try {
    const response = await apiClient.post('/agents/autonomous/knowledge/transfer', {
      source_platform: knowledgeForm.sourcePlatform,
      target_platform: knowledgeForm.targetPlatform,
      knowledge_type: knowledgeForm.knowledgeType
    })
    
    if (response.data.status === 'success') {
      if (response.data.transferred) {
        ElMessage.success('知识迁移成功')
      } else {
        ElMessage.info('无可迁移的知识')
      }
      fetchTransferStats()
    }
  } catch (error: any) {
    ElMessage.error('知识迁移失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    transferring.value = false
  }
}

// ==================== Phase 5: 工作流管理 ====================

// 获取工作流列表
const fetchWorkflows = async () => {
  loadingWorkflows.value = true
  try {
    const response = await apiClient.get('/agents/autonomous/workflow/list')
    if (response.data.status === 'success') {
      workflows.value = response.data.workflows
    }
  } catch (error: any) {
    console.error('获取工作流列表失败:', error)
  } finally {
    loadingWorkflows.value = false
  }
}

// 创建并执行工作流
const createAndExecuteWorkflow = async () => {
  if (!workflowForm.name || !workflowForm.description) {
    ElMessage.warning('请填写工作流名称和目标描述')
    return
  }
  
  creatingWorkflow.value = true
  try {
    // 先分解目标
    const decomposeResponse = await apiClient.post('/agents/autonomous/planning/decompose', {
      description: workflowForm.description,
      priority: 8
    })
    
    if (decomposeResponse.data.status !== 'success') {
      throw new Error('目标分解失败')
    }
    
    // 然后执行工作流
    const executeResponse = await apiClient.post('/agents/autonomous/workflow/execute', {
      name: workflowForm.name,
      description: workflowForm.description,
      tasks: decomposeResponse.data.tasks
    })
    
    if (executeResponse.data.status === 'success') {
      ElMessage.success('工作流创建并开始执行')
      showWorkflowDialog.value = false
      workflowForm.name = ''
      workflowForm.description = ''
      fetchWorkflows()
    }
  } catch (error: any) {
    ElMessage.error('创建工作流失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    creatingWorkflow.value = false
  }
}

// 查看工作流状态
const viewWorkflowStatus = async (workflow: any) => {
  try {
    const response = await apiClient.get(`/agents/autonomous/workflow/${workflow.workflow_id}/status`)
    if (response.data.status === 'success') {
      currentWorkflow.value = response.data.data
      showWorkflowStatusDialog.value = true
    }
  } catch (error: any) {
    ElMessage.error('获取工作流状态失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 执行工作流
const executeWorkflow = async (workflow: any) => {
  try {
    const response = await apiClient.post('/agents/autonomous/workflow/execute', {
      name: workflow.name,
      description: workflow.description || '',
      tasks: [] // 实际应该从已有任务中获取
    })
    
    if (response.data.status === 'success') {
      ElMessage.success('工作流开始执行')
      fetchWorkflows()
    }
  } catch (error: any) {
    ElMessage.error('执行工作流失败: ' + (error.response?.data?.detail || error.message))
  }
}

// ==================== Phase 6: 学习洞察 ====================

// 获取学习洞察
const fetchLearningInsights = async () => {
  try {
    const response = await apiClient.get(`/agents/autonomous/learning/insights/${selectedAgentType.value}`)
    if (response.data.status === 'success') {
      learningInsights.value = response.data.insights
    }
  } catch (error: any) {
    console.error('获取学习洞察失败:', error)
  }
}

// ==================== Phase 6: A/B测试 ====================

// 获取A/B测试列表（简化版，实际需要后端支持）
const fetchABTests = async () => {
  loadingABTests.value = true
  try {
    // 这里假设有一个获取测试列表的API，如果没有可以暂时注释
    // const response = await apiClient.get('/agents/autonomous/ab-test/list')
    // if (response.data.status === 'success') {
    //   abTests.value = response.data.tests
    // }
    abTests.value = [] // 暂时为空
  } catch (error: any) {
    console.error('获取A/B测试列表失败:', error)
  } finally {
    loadingABTests.value = false
  }
}

// 创建A/B测试
const createABTest = async () => {
  if (!abTestForm.test_name || !abTestForm.variantsText) {
    ElMessage.warning('请填写测试名称和变体列表')
    return
  }
  
  const variants = abTestForm.variantsText.split(',').map(s => s.trim()).filter(s => s)
  if (variants.length < 2) {
    ElMessage.warning('至少需要2个变体')
    return
  }
  
  creatingABTest.value = true
  try {
    const response = await apiClient.post('/agents/autonomous/ab-test/create', {
      test_name: abTestForm.test_name,
      variants: variants,
      metric: abTestForm.metric
    })
    
    if (response.data.status === 'success') {
      ElMessage.success('A/B测试创建成功')
      showABTestDialog.value = false
      abTestForm.test_name = ''
      abTestForm.variantsText = ''
      fetchABTests()
    }
  } catch (error: any) {
    ElMessage.error('创建A/B测试失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    creatingABTest.value = false
  }
}

// 分析A/B测试结果
const analyzeABTest = async (testId: string) => {
  try {
    const response = await apiClient.get(`/agents/autonomous/ab-test/${testId}/analyze`)
    if (response.data.status === 'success') {
      abTestAnalysis.value = response.data.analysis
      showABTestResultDialog.value = true
    }
  } catch (error: any) {
    ElMessage.error('分析A/B测试失败: ' + (error.response?.data?.detail || error.message))
  }
}

// ==================== Phase 6: 性能分析 ====================

// 获取性能分析
const fetchPerformanceAnalysis = async () => {
  try {
    const response = await apiClient.get(`/agents/autonomous/analytics/performance/${selectedAgentTypeForPerformance.value}`)
    if (response.data.status === 'success') {
      const agentData = response.data.report.agents[selectedAgentTypeForPerformance.value]
      performanceData.value = agentData || {}
    }
  } catch (error: any) {
    console.error('获取性能分析失败:', error)
  }
}

// 获取优化建议
const fetchOptimizationSuggestions = async () => {
  try {
    const response = await apiClient.get(`/agents/autonomous/analytics/suggestions/${selectedAgentTypeForPerformance.value}`)
    if (response.data.status === 'success') {
      optimizationSuggestions.value = response.data.suggestions
    }
  } catch (error: any) {
    console.error('获取优化建议失败:', error)
  }
}

// 初始化
onMounted(() => {
  fetchSystemStatus()
  fetchRLStats()
  fetchTransferStats()
  fetchAgentsList()
  fetchExecutionHistory()
  fetchExecutionStats()
  
  // Phase 5: 初始化工作流
  fetchWorkflows()
  
  // Phase 6: 初始化学习洞察和性能分析
  fetchLearningInsights()
  fetchPerformanceAnalysis()
  fetchOptimizationSuggestions()
  fetchABTests()
})
</script>

<style scoped>
.autonomous-agent-monitor {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
