<?xml version="1.0" encoding="UTF-8"?>
<!-- 统一集成格式 → B(Oracle) 学生格式 -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <Students>
      <xsl:for-each select="Students/student">
        <student>
          <id><xsl:value-of select="id"/></id>
          <name><xsl:value-of select="name"/></name>
          <sex><xsl:value-of select="sex"/></sex>
          <major><xsl:value-of select="major"/></major>
          <grade>2024</grade>
          <phone/>
          <status>ACTIVE</status>
        </student>
      </xsl:for-each>
    </Students>
  </xsl:template>

</xsl:stylesheet>
