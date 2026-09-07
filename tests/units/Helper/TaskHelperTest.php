<?php

namespace KanboardTests\units\Helper;

use KanboardTests\units\Base;
use Kanboard\Helper\TaskHelper;

class TaskHelperTest extends Base
{
    public function testSelectPriority()
    {
        $helper = new TaskHelper($this->container);
        $this->assertNotEmpty($helper->renderPriorityField(array('priority_end' => '1', 'priority_start' => '5', 'priority_default' => '2'), array()));
        $this->assertNotEmpty($helper->renderPriorityField(array('priority_end' => '3', 'priority_start' => '1', 'priority_default' => '2'), array()));
    }

    public function testFormatPriority()
    {
        $helper = new TaskHelper($this->container);

        $this->assertEquals(
            '<span class="task-priority priority-high" title="Task priority"><span class="ui-helper-hidden-accessible">Task priority </span><span class="priority-icon">■</span> High</span>',
            $helper->renderPriority(2)
        );

        $this->assertEquals(
            '<span class="task-priority " title="Task priority"><span class="ui-helper-hidden-accessible">Task priority </span>P-6</span>',
            $helper->renderPriority(-6)
        );
    }
}
