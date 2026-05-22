<?xml version="1.0" encoding="UTF-8"?>
<!-- 课程汇总视图: 将完整课程XML转为汇总统计视图 -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <CourseSummary>
      <total><xsl:value-of select="count(Classes/class)"/></total>
      <shared><xsl:value-of select="count(Classes/class[share_flag='Y'])"/></shared>
      <xsl:for-each select="Classes/class[share_flag='Y']">
        <shared_course>
          <id><xsl:value-of select="id"/></id>
          <name><xsl:value-of select="name"/></name>
          <college><xsl:value-of select="share_college"/></college>
        </shared_course>
      </xsl:for-each>
    </CourseSummary>
  </xsl:template>

</xsl:stylesheet>
