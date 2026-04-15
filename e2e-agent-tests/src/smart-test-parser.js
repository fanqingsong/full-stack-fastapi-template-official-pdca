#!/usr/bin/env node
/**
 * 智能测试解析器
 * 支持多种测试格式的解析和执行
 */

const fs = require('fs');
const path = require('path');

class SmartTestParser {
    constructor() {
        this.baseUrl = process.env.BASE_URL || 'http://localhost:5173';
    }

    parseTestFile(filePath) {
        const content = fs.readFileSync(filePath, 'utf-8');
        const test = {
            name: '',
            priority: '',
            description: '',
            preconditions: [],
            steps: [],
            expectedResults: [],
            testData: {}
        };

        // 解析基本信息
        const titleMatch = content.match(/^#\s+(.+)/m);
        if (titleMatch) {
            test.name = titleMatch[1].trim();
        }

        const priorityMatch = content.match(/##\s+Priority\s*\n\s*([^\n]+)/i);
        if (priorityMatch) {
            test.priority = priorityMatch[1].trim();
        }

        const descMatch = content.match(/##\s+Description\s*\n([\s\S]*?)(?=##|\Z)/i);
        if (descMatch) {
            test.description = descMatch[1].trim();
        }

        // 解析前置条件
        const precondMatch = content.match(/##\s+Pre-conditions\s*\n([\s\S]*?)(?=##|\Z)/i);
        if (precondMatch) {
            test.preconditions = this.extractListItems(precondMatch[1]);
        }

        // 解析测试步骤
        const stepsMatch = content.match(/##\s+Test\s+Steps\s*\n([\s\S]+?)(?=\n##\s+Expected Results|\Z)/i);
        if (stepsMatch) {
            test.steps = this.parseSteps(stepsMatch[1]);
        }

        // 解析预期结果
        const expectedMatch = content.match(/##\s+Expected Results\s*\n([\s\S]*?)(?=##|\Z)/i);
        if (expectedMatch) {
            test.expectedResults = this.extractListItems(expectedMatch[1]);
        }

        // 解析测试数据
        const testDataMatch = content.match(/##\s+Test Data\s*\n([\s\S]*?)$/i);
        if (testDataMatch) {
            test.testData = this.parseTestData(testDataMatch[1]);
        }

        return test;
    }

    parseSteps(content) {
        const steps = [];
        let stepIndex = 0;
        let currentStep = null;
        const lines = content.split('\n');

        for (const line of lines) {
            const trimmed = line.trim();

            // 匹配步骤标题
            const stepMatch = trimmed.match(/^###\s+Step\s+\d+:\s*(.+)$/i);
            if (stepMatch) {
                if (currentStep) {
                    steps.push(currentStep);
                }
                stepIndex++;
                currentStep = {
                    number: stepIndex,
                    description: stepMatch[1],
                    actions: []
                };
                continue;
            }

            // 解析操作
            if (currentStep && trimmed.match(/^\d+\.\s*/)) {
                const action = this.parseStepAction(trimmed);
                if (action) {
                    currentStep.actions.push(action);
                }
            }
        }

        if (currentStep) {
            steps.push(currentStep);
        }

        return steps;
    }

    parseStepAction(text) {
        // 移除数字前缀
        const actionText = text.replace(/^\d+\.\s*/, '').trim();

        // Navigate/Open operations
        if (actionText.match(/Navigate to|Open|Go to/i)) {
            const urlMatch = actionText.match(/(navigate to|open|go to)\s+(.+)/i);
            if (urlMatch) {
                let url = urlMatch[2].trim();
                if (url === 'BASE_URL') {
                    url = this.baseUrl;
                }
                return {
                    type: 'navigate',
                    target: url,
                    description: actionText
                };
            }
        }

        // Enter/Fill operations
        if (actionText.match(/Enter|Fill|Type/i)) {
            const emailMatch = actionText.match(/Enter email:\s*(.+)/i);
            if (emailMatch) {
                return {
                    type: 'fill',
                    target: 'email',
                    value: emailMatch[1].trim(),
                    description: actionText
                };
            }

            const passwordMatch = actionText.match(/Enter password:\s*(.+)/i);
            if (passwordMatch) {
                return {
                    type: 'fill',
                    target: 'password',
                    value: passwordMatch[1].trim(),
                    description: actionText
                };
            }

            const fillMatch = actionText.match(/(?:Enter|Fill|Type)\s+(.+?)\s+(?:in|for|as)\s+(.+)/i);
            if (fillMatch) {
                return {
                    type: 'fill',
                    target: fillMatch[2].trim(),
                    value: fillMatch[1].trim(),
                    description: actionText
                };
            }
        }

        // Click operations
        if (actionText.match(/Click|Press/i)) {
            const buttonMatch = actionText.match(/(?:Click|Press)\s+(?:the\s+)?["']?(.+?)["']?\s+button/i);
            if (buttonMatch) {
                return {
                    type: 'click',
                    target: buttonMatch[1].trim(),
                    description: actionText
                };
            }

            const clickMatch = actionText.match(/(?:Click|Press)\s+(.+)/i);
            if (clickMatch) {
                return {
                    type: 'click',
                    target: clickMatch[1].replace(/\s+(?:button|link|element)$/, '').trim(),
                    description: actionText
                };
            }
        }

        // Verify operations
        if (actionText.match(/Verify|Check|Ensure|Assert/i)) {
            const urlMatch = actionText.match(/(?:verify|check|ensure|assert)\s+(?:that\s+)?(?:the\s+)?URL\s+(?:changes?\s+to\s+(?:contain\s+)?["']?)(.+?)(?:["']|$)/i);
            if (urlMatch) {
                return {
                    type: 'verify-url',
                    target: urlMatch[1].trim(),
                    description: actionText
                };
            }

            const visibilityMatch = actionText.match(/(?:verify|check|ensure|assert)\s+(?:that\s+)?(.+?)\s+(?:is\s+)?visible/i);
            if (visibilityMatch) {
                return {
                    type: 'verify-visible',
                    target: visibilityMatch[1].trim(),
                    description: actionText
                };
            }

            const verifyMatch = actionText.match(/(?:Verify|Check|Ensure|Assert)\s+(?:that\s+)?(.+)/i);
            if (verifyMatch) {
                return {
                    type: 'verify',
                    target: verifyMatch[1].trim(),
                    description: actionText
                };
            }
        }

        // Wait operations
        if (actionText.match(/Wait|Delay/i)) {
            const waitMatch = actionText.match(/(?:wait|delay)\s+(?:for\s+)?(\d+)\s*(?:seconds?|secs?|s)?/i);
            if (waitMatch) {
                return {
                    type: 'wait',
                    duration: parseInt(waitMatch[1]) * 1000,
                    description: actionText
                };
            }

            return {
                type: 'wait',
                duration: 1000,
                description: actionText
            };
        }

        // Refresh operation
        if (actionText.match(/Refresh|Reload/i)) {
            return {
                type: 'refresh',
                description: actionText
            };
        }

        // 如果无法识别，返回通用操作
        return {
            type: 'unknown',
            description: actionText
        };
    }

    extractListItems(content) {
        const items = [];
        const lines = content.split('\n');
        for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith('-') || trimmed.match(/^\d+\./)) {
                items.push(trimmed.replace(/^[-\d.]+/, '').trim());
            }
        }
        return items;
    }

    parseTestData(content) {
        const data = {};
        const lines = content.split('\n');
        let currentSection = null;

        for (const line of lines) {
            const trimmed = line.trim();

            // Match sections like "User 1:", "Expected behavior:", etc.
            const sectionMatch = trimmed.match(/^([^:]+):$/);
            if (sectionMatch) {
                currentSection = sectionMatch[1].trim().toLowerCase().replace(/\s+/g, '_');
                data[currentSection] = [];
                continue;
            }

            // Match key-value pairs
            const kvMatch = trimmed.match(/^([^:]+):\s*(.+)$/);
            if (kvMatch) {
                const key = kvMatch[1].trim().toLowerCase().replace(/\s+/g, '_');
                const value = kvMatch[2].trim();
                data[key] = value;
            }

            // Add to current section
            if (currentSection && trimmed && !trimmed.match(/^#+/)) {
                data[currentSection].push(trimmed);
            }
        }

        return data;
    }

    generateExecutableScript(test) {
        console.log(`\n🎯 生成可执行脚本: ${test.name}`);
        console.log(`📋 优先级: ${test.priority}`);
        console.log(`📝 描述: ${test.description.substring(0, 100)}...`);

        const script = {
            test: test.name,
            baseUrl: this.baseUrl,
            steps: test.steps.map(step => ({
                description: step.description,
                actions: step.actions.map(action => this.generateActionCode(action))
            }))
        };

        console.log(`📊 总步骤数: ${test.steps.length}`);
        console.log(`🔧 总操作数: ${test.steps.reduce((sum, step) => sum + step.actions.length, 0)}`);

        return script;
    }

    generateActionCode(action) {
        switch (action.type) {
            case 'navigate':
                return `await navigateTo('${action.target}');`;

            case 'fill':
                return `await fillField('${action.target}', '${action.value}');`;

            case 'click':
                return `await clickElement('${action.target}');`;

            case 'verify':
            case 'verify-url':
            case 'verify-visible':
                return `await verify('${action.target}');`;

            case 'wait':
                return `await wait(${action.duration});`;

            case 'refresh':
                return `await refresh();`;

            default:
                return `// ${action.description}`;
        }
    }

    validateTest(test) {
        const issues = [];

        if (!test.name) {
            issues.push('缺少测试名称');
        }

        if (test.steps.length === 0) {
            issues.push('没有测试步骤');
        }

        test.steps.forEach((step, index) => {
            if (!step.description) {
                issues.push(`步骤 ${index + 1}: 缺少描述`);
            }
            if (step.actions.length === 0) {
                issues.push(`步骤 ${index + 1}: 没有操作`);
            }
        });

        return issues;
    }

    printTestSummary(test) {
        console.log('\n' + '='.repeat(60));
        console.log(`📋 测试: ${test.name}`);
        console.log('='.repeat(60));
        console.log(`🎯 优先级: ${test.priority}`);
        console.log(`📝 描述: ${test.description}`);
        console.log(`📊 步骤数: ${test.steps.length}`);

        if (test.preconditions.length > 0) {
            console.log(`\n🔑 前置条件:`);
            test.preconditions.forEach((cond, i) => {
                console.log(`   ${i + 1}. ${cond}`);
            });
        }

        console.log(`\n📝 测试步骤:`);
        test.steps.forEach((step, i) => {
            console.log(`\n   步骤 ${step.number}: ${step.description}`);
            step.actions.forEach((action, j) => {
                console.log(`      ${j + 1}. ${action.description}`);
            });
        });

        if (test.expectedResults.length > 0) {
            console.log(`\n✅ 预期结果:`);
            test.expectedResults.forEach((result, i) => {
                console.log(`   ${i + 1}. ${result}`);
            });
        }

        console.log('\n' + '='.repeat(60));
    }
}

// String.prototype.findall polyfill
if (!String.prototype.findall) {
    String.prototype.findall = function(regex) {
        const matches = [];
        let match;
        const globalRegex = new RegExp(regex.source, regex.flags + 'g');
        while ((match = globalRegex.exec(this)) !== null) {
            matches.push(match);
        }
        return matches;
    };
}

// 主执行函数
async function main() {
    const parser = new SmartTestParser();

    const args = process.argv.slice(2);
    if (args.length === 0) {
        console.log('用法: node smart-test-parser.js <test-file>');
        process.exit(1);
    }

    const testFile = args[0];
    if (!fs.existsSync(testFile)) {
        console.error(`❌ 测试文件不存在: ${testFile}`);
        process.exit(1);
    }

    try {
        const test = parser.parseTestFile(testFile);
        const issues = parser.validateTest(test);

        if (issues.length > 0) {
            console.log('❌ 发现问题:');
            issues.forEach(issue => console.log(`   - ${issue}`));
            process.exit(1);
        }

        parser.printTestSummary(test);
        parser.generateExecutableScript(test);

        console.log('\n✅ 测试解析成功！');
        console.log('🚀 测试结构有效，框架已准备就绪');

    } catch (error) {
        console.error('❌ 解析错误:', error.message);
        console.error(error.stack);
        process.exit(1);
    }
}

if (require.main === module) {
    main().catch(error => {
        console.error('致命错误:', error);
        process.exit(1);
    });
}

module.exports = SmartTestParser;